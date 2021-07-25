#!/usr/bin/env python

from plumbum import cli, FG
from plumbum.cmd import rm

from bet_mask import bet_mask
from util import BET_THRESHOLD, logfmt, pjoin, B0_THRESHOLD, REPOL_BSHELL_GREATER
from shutil import copyfile
from _eddy_config import obtain_fsl_eddy_params
from util import save_nifti, load_nifti
from conversion import read_bvals, read_bvecs, write_bvecs
import numpy as np

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class Eddy(cli.Application):
    '''Eddy correction using eddy_openmp/cuda command in fsl
    For more info, see https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide
    You can also view the help message typing:
    `eddy_openmp` or `eddy_cuda`
    '''

    dwi_file= cli.SwitchAttr(
        ['--dwi'],
        cli.ExistingFile,
        help='nifti DWI image)',
        mandatory=True)

    bvecs_file= cli.SwitchAttr(
        ['--bvecs'],
        cli.ExistingFile,
        help='bvecs file of the DWI)',
        mandatory=True)

    bvals_file= cli.SwitchAttr(
        ['--bvals'],
        cli.ExistingFile,
        help='bvals file of the DWI)',
        mandatory=True)

    b0_brain_mask= cli.SwitchAttr(
        ['--mask'],
        cli.ExistingFile,
        help='mask for the DWI; if not provided, a mask is created using fsl bet',
        mandatory=False)

    acqparams_file= cli.SwitchAttr(
        ['--acqp'],
        cli.ExistingFile,
        help='acuisition parameters file (.txt)',
        mandatory=True)

    eddy_config_file= cli.SwitchAttr(
        ['--config'],
        cli.ExistingFile,
        help='''config file for FSL eddy tools; see scripts/eddy_config.txt; 
                copy this file to your directory, edit relevant sections, and provide as --config /path/to/my/eddy_config.txt''',
        mandatory=True)

    index_file= cli.SwitchAttr(
        ['--index'],
        cli.ExistingFile,
        help='mapping file (.txt) for each gradient --> acquisition parameters',
        mandatory=True)

    betThreshold = cli.SwitchAttr(
        '-f',
        help= 'threshold for fsl bet mask',
        mandatory=False,
        default= BET_THRESHOLD)

    outDir= cli.SwitchAttr(
        ['--out'],
        cli.NonexistentPath,
        help='output directory',
        mandatory=True)

    useGpu= cli.Flag(
        ['--eddy-cuda'],
        help='use eddy_cuda instead of eddy_openmp, requires fsl/bin/eddy_cuda and nvcc in PATH')

    def main(self):

        from plumbum.cmd import eddy_openmp
        
        if self.useGpu:
            try:
                from plumbum.cmd import nvcc
                nvcc['--version'] & FG
                
                print('\nCUDA found, looking for available GPU\n')
                from GPUtil import getFirstAvailable
                getFirstAvailable()
                
                print('available GPU found, looking for eddy_cuda executable\n'
                      'make sure you have created a softlink according to '
                      'https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide')
                from plumbum.cmd import eddy_cuda as eddy_openmp

                print('\neddy_cuda executable found\n')
            except:
                print('nvcc, available GPU, and/or eddy_cuda was not found, using eddy_openmp')


        prefix= self.dwi_file.name.split('.')[0]
        self.outDir.mkdir()
        outPrefix = pjoin(self.outDir._path, prefix+'_Ed')


        if not self.b0_brain_mask:
            logging.info('Mask not provided, creating mask ...')

            self.b0_brain_mask = outPrefix + '_mask.nii.gz'

            bet_mask(self.dwi_file, self.b0_brain_mask, 4, bvalFile= self.bvals_file, BET_THRESHOLD= self.betThreshold)


        _, _, eddy_openmp_params= obtain_fsl_eddy_params(self.eddy_config_file._path)
        
        print('eddy_openmp/cuda parameters')
        print(eddy_openmp_params)
        print('')
        
        eddy_openmp[f'--imain={self.dwi_file}',
                    f'--mask={self.b0_brain_mask}',
                    f'--acqp={self.acqparams_file}',
                    f'--index={self.index_file}',
                    f'--bvecs={self.bvecs_file}',
                    f'--bvals={self.bvals_file}',
                    f'--out={outPrefix}',
                    eddy_openmp_params.split()] & FG
        
        # free space, see https://github.com/pnlbwh/pnlNipype/issues/82
        if '--repol' in eddy_openmp_params:
            rm[f'{outPrefix}.eddy_outlier_free_data.nii.gz'] & FG
        
        
        bvals= np.array(read_bvals(self.bvals_file))
        ind= [i for i in range(len(bvals)) if bvals[i]>B0_THRESHOLD and bvals[i]<= REPOL_BSHELL_GREATER]
        
        if '--repol' in eddy_openmp_params and len(ind):
            
            print('\nDoing eddy_openmp/cuda again without --repol option '
                  'to obtain eddy correction w/o outlier replacement for b<=500 shells\n')

            eddy_openmp_params= eddy_openmp_params.split()
            eddy_openmp_params.remove('--repol')
            print(eddy_openmp_params)
            print('')
            wo_repol_outDir= self.outDir.join('wo_repol')
            wo_repol_outDir.mkdir()
            wo_repol_outPrefix = pjoin(wo_repol_outDir, prefix + '_Ed')

            eddy_openmp[f'--imain={self.dwi_file}',
                        f'--mask={self.b0_brain_mask}',
                        f'--acqp={self.acqparams_file}',
                        f'--index={self.index_file}',
                        f'--bvecs={self.bvecs_file}',
                        f'--bvals={self.bvals_file}',
                        f'--out={wo_repol_outPrefix}',
                        eddy_openmp_params] & FG


            repol_bvecs= np.array(read_bvecs(outPrefix + '.eddy_rotated_bvecs'))
            wo_repol_bvecs= np.array(read_bvecs(wo_repol_outPrefix + '.eddy_rotated_bvecs'))

            merged_bvecs= repol_bvecs.copy()
            merged_bvecs[ind,: ]= wo_repol_bvecs[ind,: ]

            repol_data= load_nifti(outPrefix + '.nii.gz')
            wo_repol_data= load_nifti(wo_repol_outPrefix + '.nii.gz')
            merged_data= repol_data.get_fdata().copy()
            merged_data[...,ind]= wo_repol_data.get_fdata()[...,ind]

            save_nifti(outPrefix + '.nii.gz', merged_data, repol_data.affine, hdr=repol_data.header)
            
            # copy bval,bvec to have same prefix as that of eddy corrected volume
            write_bvecs(outPrefix + '.bvec', merged_bvecs)
            copyfile(self.bvals_file, outPrefix + '.bval')
            
            # clean up
            rm['-r', wo_repol_outDir] & FG
            
        else:
            # copy bval,bvec to have same prefix as that of eddy corrected volume
            copyfile(outPrefix + '.eddy_rotated_bvecs', outPrefix + '.bvec')
            copyfile(self.bvals_file, outPrefix + '.bval')


if __name__== '__main__':
    Eddy.run()
    
