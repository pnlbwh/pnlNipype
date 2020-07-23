#!/usr/bin/env python

from plumbum import cli, FG, local
from plumbum.cmd import topup, applytopup, fslmaths, rm, fslmerge, cat, bet, gzip

try:
    from plumbum.cmd import nvcc
    nvcc['--version'] & FG
    print('\nCUDA found, looking for eddy_cuda executable\n'
          'make sure you have created a softlink according to '
          'https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide')
    from plumbum.cmd import eddy_cuda as eddy_openmp
    print('eddy_cuda executable found\n')
except:
    from plumbum.cmd import eddy_openmp

from util import BET_THRESHOLD, TemporaryDirectory, logfmt, load_nifti, FILEDIR, \
    REPOL_BSHELL_GREATER, save_nifti, B0_THRESHOLD
from os.path import join as pjoin, abspath, basename
from subprocess import check_call
from os import environ
from shutil import copyfile
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs
from _eddy_config import obtain_fsl_eddy_params
from nibabel import load
import numpy as np


FSLDIR=environ['FSLDIR']

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def obtainB0(inVol, bvalFile, outVol, num_b0):

    if num_b0 == '1':
        check_call((' ').join([pjoin(FILEDIR,'bse.py'), '-i', inVol, '--bvals', bvalFile, '-o', outVol]), shell=True)
    elif num_b0 == '-1':
        check_call((' ').join([pjoin(FILEDIR,'bse.py'), '-i', inVol, '--bvals', bvalFile, '-o', outVol, '--all']), shell=True)
    else:
        raise ValueError('Invalid --numb0')


class TopupEddyEpi(cli.Application):
    '''Epi and eddy correction using topup and eddy_openmp/cuda commands in fsl
    For more info, see:
        https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide
        https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/TopupUsersGuide
    You can also view the help message:
        `eddy_openmp` or `eddy_cuda`
        `topup`
    '''

    dwi_file= cli.SwitchAttr(
        ['--imain'],
        help='''--dwi primary4D,secondary4D/3D
                primary: one 4D volume input, should be PA;
                secondary: another 3D/4D volume input, should be AP, which is opposite of primary 4D volume''',
        mandatory=True)

    b0_brain_mask= cli.SwitchAttr(
        ['--mask'],
        help='''--mask primaryB0mask,secondaryB0mask''',
        mandatory=False)

    bvecs_file= cli.SwitchAttr(
        ['--bvecs'],
        help='''--bvecs primaryBvec,secondaryBvec
                --bvecs primaryBvec
                if only one bvec file is provided, 
                the second bvec file is either assumed same (secondary4D) or "0.0 0.0 0.0" (secondary3D)''',
        mandatory=True)


    bvals_file= cli.SwitchAttr(
        ['--bvals'],
        help='''--bvals primaryBval,secondaryBval
                --bvals primaryBval
                if only one bval file is provided, 
                the second bval file is either assumed same (secondary4D) or "0.0" (secondary3D)''',
        mandatory=True)


    acqparams_file= cli.SwitchAttr(
        ['--acqp'],
        cli.ExistingFile,
        help='acuisition parameters file (.txt) containing TWO lines, first for primary4D (PA), second for secondary4D/3D(AP)',
        mandatory=True)

    eddy_config_file= cli.SwitchAttr(
        ['--config'],
        cli.ExistingFile,
        help='''config file for FSL eddy tools; see scripts/eddy_config.txt; 
                copy this file to your directory, edit relevant sections, and provide as --config /path/to/my/eddy_config.txt''',
        mandatory=True)

    betThreshold= cli.SwitchAttr(
        '-f',
        help= 'threshold for fsl bet mask',
        mandatory=False,
        default= BET_THRESHOLD)


    outDir= cli.SwitchAttr(
        ['--out'],
        cli.NonexistentPath,
        help='output directory',
        mandatory=True)

    num_b0= cli.SwitchAttr(
        ['--numb0'],
        help='number of b0 images to use from primary and secondary (if 4D): 1 for first b0 only, -1 for all the b0s',
        mandatory=False,
        default=True)

    whichVol= cli.SwitchAttr(
        ['--whichVol'],
        help='which volume(s) to correct through eddy: 1(only primary4D) or 1,2(primary4D+secondary4D/3D)',
        mandatory=False,
        default=True)

    # force= cli.Flag(
    #     '--force',
    #     help= 'overwrite output directory',
    #     default= False)



    def main(self):
        
        
        def _eddy_openmp(modData, modBvals, modBvecs, eddy_openmp_params):
            
            print('eddy_openmp/cuda parameters')
            print(eddy_openmp_params)
            print('')

            eddy_openmp[f'--imain={modData}',
                        f'--mask={topupMask}',
                        f'--acqp={self.acqparams_file}',
                        f'--index={indexFile}',
                        f'--bvecs={modBvecs}',
                        f'--bvals={modBvals}',
                        f'--out={outPrefix}',
                        f'--topup={topup_results}',
                        '--verbose',
                        eddy_openmp_params.split()] & FG


            bvals = np.array(read_bvals(modBvals))
            ind= [i for i in range(len(bvals)) if bvals[i]>B0_THRESHOLD and bvals[i]<= REPOL_BSHELL_GREATER]

            if '--repol' in eddy_openmp_params and len(ind):

                print('\nDoing eddy_openmp/cuda again without --repol option '
                      'to obtain eddy correction w/o outlier replacement for b<=500 shells\n')

                eddy_openmp_params = eddy_openmp_params.split()
                eddy_openmp_params.remove('--repol')
                print(eddy_openmp_params)
                print('')
                wo_repol_outDir = local.path(outPrefix).dirname.join('wo_repol')
                wo_repol_outDir.mkdir()
                # prefix= basename(outPrefix)
                wo_repol_outPrefix = pjoin(wo_repol_outDir, basename(outPrefix))


                eddy_openmp[f'--imain={modData}',
                            f'--mask={topupMask}',
                            f'--acqp={self.acqparams_file}',
                            f'--index={indexFile}',
                            f'--bvecs={modBvecs}',
                            f'--bvals={modBvals}',
                            f'--out={wo_repol_outPrefix}',
                            f'--topup={topup_results}',
                            '--verbose',
                            eddy_openmp_params] & FG


                repol_bvecs = np.array(read_bvecs(outPrefix + '.eddy_rotated_bvecs'))
                wo_repol_bvecs = np.array(read_bvecs(wo_repol_outPrefix + '.eddy_rotated_bvecs'))

                merged_bvecs = repol_bvecs.copy()
                merged_bvecs[ind, :] = wo_repol_bvecs[ind, :]

                repol_data = load(outPrefix + '.nii.gz')
                wo_repol_data = load(wo_repol_outPrefix + '.nii.gz')
                merged_data = repol_data.get_fdata().copy()
                merged_data[..., ind] = wo_repol_data.get_fdata()[..., ind]

                save_nifti(outPrefix + '.nii.gz', merged_data, repol_data.affine, hdr=repol_data.header)

                # copy bval,bvec to have same prefix as that of eddy corrected volume
                write_bvecs(outPrefix + '.bvec', merged_bvecs)
                copyfile(modBvals, outPrefix + '.bval')

            else:
                # copy bval,bvec to have same prefix as that of eddy corrected volume
                copyfile(outPrefix + '.eddy_rotated_bvecs', outPrefix + '.bvec')
                copyfile(modBvals, outPrefix + '.bval')
        



        # if self.force:
        #     logging.info('Deleting previous output directory')
        #     rm('-rf', self.outDir)


        temp= self.dwi_file.split(',')
        primaryVol= abspath(temp[0])
        if len(temp)<2:
            raise AttributeError('Two volumes are required for --imain')
        else:
            secondaryVol= abspath(temp[1])

        if self.b0_brain_mask:
            temp = self.b0_brain_mask.split(',')
            primaryMask = abspath(temp[0])
            if len(temp) == 2:
                secondaryMask = abspath(temp[1])
            else:
                secondaryMask = abspath(temp[0])

        else:
            primaryMask=[]
            secondaryMask=[]


        # obtain 4D/3D info and time axis info
        dimension = load_nifti(primaryVol).header['dim']
        dim1 = dimension[0]
        if dim1!=4:
            raise AttributeError('primary volume must be 4D, however, secondary can be 3D/4D')
        numVol1 = dimension[4]

        dimension = load_nifti(secondaryVol).header['dim']
        dim2 = dimension[0]
        numVol2 = dimension[4]


        temp= self.bvals_file.split(',')
        if len(temp)>=1:
            primaryBval= abspath(temp[0])
        if len(temp)==2:
            secondaryBval= abspath(temp[1])
        elif len(temp)==1 and dim2==4:
            secondaryBval= primaryBval
        elif len(temp)==1 and dim2==3:
            secondaryBval=[]
        elif len(temp)==0:
            raise AttributeError('--bvals are required')

        temp= self.bvecs_file.split(',')
        if len(temp)>=1:
            primaryBvec= abspath(temp[0])
        if len(temp)==2:
            secondaryBvec= abspath(temp[1])
        elif len(temp) == 1 and dim2 == 4:
            secondaryBvec = primaryBvec
        elif len(temp)==1 and dim2==3:
            secondaryBvec=[]
        else:
            raise AttributeError('--bvecs are required')



        with TemporaryDirectory() as tmpdir:

            tmpdir= local.path(tmpdir)

            # mask both volumes, fslmaths can do that irrespective of dimension
            logging.info('Masking the volumes')

            primaryMaskedVol = tmpdir / 'primaryMasked.nii.gz'
            secondaryMaskedVol = tmpdir / 'secondaryMasked.nii.gz'

            if primaryMask:
                # mask the volume
                fslmaths[primaryVol, '-mas', primaryMask, primaryMaskedVol] & FG
            else:
                primaryMaskedVol= primaryVol

            if secondaryMask:
                # mask the volume
                fslmaths[secondaryVol, '-mas', secondaryMask, secondaryMaskedVol] & FG
            else:
                secondaryMaskedVol= secondaryVol


            logging.info('Extracting B0 from masked volumes')
            B0_PA= tmpdir / 'B0_PA.nii.gz'
            B0_AP= tmpdir / 'B0_AP.nii.gz'

            obtainB0(primaryMaskedVol, primaryBval, B0_PA, self.num_b0)

            if dim2==4:
                obtainB0(secondaryMaskedVol, secondaryBval, B0_AP, self.num_b0)
            else:
                B0_AP= secondaryMaskedVol


            B0_PA_AP_merged = tmpdir / 'B0_PA_AP_merged.nii.gz'
            with open(self.acqparams_file._path) as f:
                acqp= f.read().split('\n')

            logging.info('Writing acqparams.txt for topup')

            # firstDim: first acqp line should be replicated this number of times
            firstB0dim= load_nifti(str(B0_PA)).header['dim'][4]
            # secondDim: second acqp line should be replicated this number of times
            secondB0dim= load_nifti(str(B0_AP)).header['dim'][4]
            acqp_topup= tmpdir / 'acqp_topup.txt'
            with open(acqp_topup,'w') as f:
                for i in range(firstB0dim):
                    f.write(acqp[0]+'\n')

                for i in range(secondB0dim):
                    f.write(acqp[1]+'\n')


            logging.info('Merging B0_PA and BO_AP')
            fslmerge('-t', B0_PA_AP_merged, B0_PA, B0_AP)


            topup_params, applytopup_params, eddy_openmp_params= obtain_fsl_eddy_params(self.eddy_config_file._path)

            # Example for topup
            # === on merged b0 images ===
            # https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide#Running_topup_on_the_b.3D0_volumes
            # topup --imain=both_b0 --datain=my_acq_param.txt --out=my_topup_results
            # === on all b0 images ===
            # https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/TopupUsersGuide#Running_topup
            # topup --imain=all_my_b0_images.nii --datain=acquisition_parameters.txt --config=b02b0.cnf --out=my_output


            logging.info('Running topup')
            topup_results= tmpdir / 'topup_results'
            topup[f'--imain={B0_PA_AP_merged}',
                  f'--datain={acqp_topup}',
                  f'--out={topup_results}',
                  '--verbose',
                  topup_params.split()] & FG



            logging.info('Running applytopup')
            
            topupMask= tmpdir / 'topup_mask.nii.gz'

            # applytopup on primary4D,secondary4D/3D
            topupOut= tmpdir / 'topup_out.nii.gz'
            if dim2==4:
                applytopup[f'--imain={primaryMaskedVol},{secondaryMaskedVol}',
                           f'--datain={self.acqparams_file}',
                           '--inindex=1,2',
                           f'--topup={topup_results}',
                           f'--out={topupOut}',
                           '--verbose',
                           applytopup_params.split()] & FG

            else:
                applytopup[f'--imain={B0_PA},{B0_AP}',
                           f'--datain={self.acqparams_file}',
                           '--inindex=1,2',
                           f'--topup={topup_results}',
                           f'--out={topupOut}',
                           '--verbose',
                           applytopup_params.split()] & FG


            topupOutMean= tmpdir / 'topup_out_mean.nii.gz'
            fslmaths[topupOut, '-Tmean', topupOutMean] & FG
            bet[topupOutMean, topupMask._path.split('_mask.nii.gz')[0], '-m', '-n'] & FG


            # another approach could be
            # threshold mean of primary,secondary mask at 0.5 and obtain modified mask, use that mask for eddy_openmp
            # fslmerge[topupMask, '-t', primaryMask, secondaryMask] & FG
            # fslmaths[topupMask, '-Tmean', topupMask] & FG
            # fslmaths[topupMask, '-thr', '0.5', topupMask, '-odt' 'char'] & FG

            logging.info('Writing index.txt for topup')
            indexFile= tmpdir / 'index.txt'
            with open(indexFile, 'w') as f:
                for i in range(numVol1):
                    f.write('1\n')


            outPrefix = tmpdir / basename(primaryVol).split('.')[0] + '_Ep_Ed'

            temp = self.whichVol.split(',')
            if len(temp)==1 and temp[0]=='1':
                # correct only primary4D volume

                # self._eddy_openmp(primaryMaskedVol, primaryBval, primaryBvec, topupMask, indexFile, outPrefix)
                _eddy_openmp(primaryMaskedVol, primaryBval, primaryBvec, eddy_openmp_params)

                # eddy_openmp[f'--imain={primaryMaskedVol}',
                #             f'--mask={topupMask}',
                #             f'--acqp={self.acqparams_file}',
                #             f'--index={indexFile}',
                #             f'--bvecs={primaryBvec}',
                #             f'--bvals={primaryBval}',
                #             f'--out={outPrefix}',
                #             f'--topup={topup_results}',
                #             '--verbose',
                #             eddy_openmp_params.split()] & FG




            elif len(temp)==2 and temp[1]=='2':
                # sylvain would like to correct both primary and secondary volumes


                with open(indexFile, 'a') as f:
                    for i in range(numVol2):
                        f.write('2\n')


                # join both bvalFiles
                bvals1= read_bvals(primaryBval)
                if dim2==4 and not secondaryBval:
                    bvals2= bvals1.copy()
                elif dim2==4 and secondaryBval:
                    bvals2= read_bvals(secondaryBval)
                elif dim2==3:
                    bvals2=[0]

                combinedBvals = tmpdir / 'combinedBvals.txt'
                write_bvals(combinedBvals, bvals1+bvals2)

                # join both bvecFiles
                bvecs1= read_bvecs(primaryBvec)
                if dim2==4 and not secondaryBvec:
                    bvecs2= bvecs1.copy()
                elif dim2==4 and secondaryBvec:
                    bvecs2= read_bvecs(secondaryBvec)
                elif dim2==3:
                    bvecs2=[[0,0,0]]

                # join both bvecFiles
                combinedBvecs = tmpdir / 'combinedBvecs.txt'
                write_bvecs(combinedBvecs, bvecs1+bvecs2)

                combinedData= tmpdir / 'combinedData.nii.gz'
                fslmerge('-t', combinedData, primaryMaskedVol, secondaryMaskedVol)


                # call self._eddy_openmp
                _eddy_openmp(combinedData, combinedBvals, combinedBvecs, eddy_openmp_params)
                
                # eddy_openmp[f'--imain={combinedData}',
                #             f'--mask={topupMask}',
                #             f'--acqp={self.acqparams_file}',
                #             f'--index={indexFile}',
                #             f'--bvecs={combinedBvecs}',
                #             f'--bvals={combinedBvals}',
                #             f'--out={outPrefix}',
                #             f'--topup={topup_results}',
                #             '--verbose',
                #             eddy_openmp_params.split()] & FG


            else:
                raise ValueError('Invalid --whichVol')


            # copy bval,bvec to have same prefix as that of eddy corrected volume
            # copyfile(outPrefix+'.eddy_rotated_bvecs', outPrefix+'.bvec')
            # copyfile(primaryBval, outPrefix+'.bval')
            
            # rename topupMask to have same prefix as that of eddy corrected volume
            topupMask.move(outPrefix+'_mask.nii.gz')

            tmpdir.move(self.outDir)


if __name__== '__main__':
    TopupEddyEpi.run()
