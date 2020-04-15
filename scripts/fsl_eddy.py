#!/usr/bin/env python

from plumbum import cli, FG
from plumbum.cmd import eddy_openmp
from bet_mask import bet_mask
from util import BET_THRESHOLD, logfmt, pjoin
from shutil import copyfile
from _eddy_config import obtain_fsl_eddy_params

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))



class Eddy(cli.Application):
    '''Eddy correction using eddy_openmp command in fsl
    For more info, see https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide
    You can also view the help message:
    eddy_openmp
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



    def main(self):


        prefix= self.dwi_file.name.split('.')[0]
        outPrefix = pjoin(self.outDir._path, prefix+'_Ed')


        if self.b0_brain_mask=='None':
            logging.info('Mask not provided, creating mask ...')

            self.b0_brain_mask = outPrefix + '_mask.nii.gz'

            bet_mask(self.dwi_file, self.b0_brain_mask, 4, bvalFile= self.bvals_file, BET_THRESHOLD= self.betThreshold)


        _, _, eddy_openmp_params= obtain_fsl_eddy_params(self.eddy_config_file._path)

        eddy_openmp[f'--imain={self.dwi_file}',
                    f'--mask={self.b0_brain_mask}',
                    f'--acqp={self.acqparams_file}',
                    f'--index={self.index_file}',
                    f'--bvecs={self.bvecs_file}',
                    f'--bvals={self.bvals_file}',
                    f'--out={outPrefix}',
                    '--verbose',
                    eddy_openmp_params.split()] & FG


        # copy bval,bvec to have same prefix as that of eddy corrected volume
        copyfile(outPrefix + '.eddy_rotated_bvecs', outPrefix + '.bvec')
        copyfile(self.bvals_file, outPrefix + '.bval')

if __name__== '__main__':
    Eddy.run()
