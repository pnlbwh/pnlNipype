#!/usr/bin/env python

from maskfilter import single_scale
from plumbum import cli, FG, local
from plumbum.cmd import topup, applytopup, fslmaths, rm, fslmerge, cat, bet, gzip, rm
from util import BET_THRESHOLD, logfmt, load_nifti, FILEDIR, \
    REPOL_BSHELL_GREATER, save_nifti, B0_THRESHOLD
from tempfile import TemporaryDirectory
from os.path import join as pjoin, abspath, basename
from subprocess import check_call
from os import environ
from shutil import copyfile, move
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs
from _eddy_config import obtain_fsl_eddy_params
import numpy as np
import re

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
        help='''--imain primary4D,secondary4D/3D
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
        default='1')

    scale= cli.SwitchAttr(
        ['--scale'],
        help='number of times erosion and dilation is performed to obtain modified mask',
        default='2')


    whichVol= cli.SwitchAttr(
        ['--whichVol'],
        help='which volume(s) to correct through eddy: 1(only primary4D) or 1,2(primary4D+secondary4D/3D)',
        mandatory=False,
        default='1')

    # force= cli.Flag(
    #     '--force',
    #     help= 'overwrite output directory',
    #     default= False)

    useGpu= cli.Flag(
        ['--eddy-cuda'],
        help='use eddy_cuda instead of eddy_openmp, requires fsl/bin/eddy_cuda and nvcc in PATH')


    def main(self):

        from plumbum.cmd import eddy_openmp

        # cli.NonexistentPath is already making sure it does not exist
        self.outDir.mkdir()

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



        def _eddy_openmp(modData, modBvals, modBvecs, eddy_openmp_params):
            
            print('eddy_openmp/cuda parameters')
            print(eddy_openmp_params)
            print('')
            
            # eddy_openmp yields as many volumes as there are input volumes
            # this is the main output and consists of the input data after correction for
            # eddy currents, subject movement, and susceptibility if --topup was specified
            
            eddy_openmp[f'--imain={modData}',
                        f'--mask={topupMask}',
                        f'--acqp={self.acqparams_file}',
                        f'--index={indexFile}',
                        f'--bvecs={modBvecs}',
                        f'--bvals={modBvals}',
                        f'--out={outPrefix}',
                        f'--topup={topup_results}',
                        eddy_openmp_params.split()] & FG


            # free space, see https://github.com/pnlbwh/pnlNipype/issues/82
            if '--repol' in eddy_openmp_params:
                rm[f'{outPrefix}.eddy_outlier_free_data.nii.gz'] & FG
                    
            bvals = np.array(read_bvals(modBvals))
            ind= [i for i in range(len(bvals)) if bvals[i]>B0_THRESHOLD and bvals[i]<= REPOL_BSHELL_GREATER]

            if '--repol' in eddy_openmp_params and len(ind):

                print('\nDoing eddy_openmp/cuda again without --repol option '
                      f'to obtain eddy correction w/o outlier replacement for b<={REPOL_BSHELL_GREATER} shells\n')

                eddy_openmp_params = eddy_openmp_params.split()
                eddy_openmp_params.remove('--repol')
                print(eddy_openmp_params)
                print('')
                wo_repol_outDir = local.path(outPrefix).dirname.join('wo_repol')
                wo_repol_outDir.mkdir()
                wo_repol_outPrefix = pjoin(wo_repol_outDir, basename(outPrefix))


                eddy_openmp[f'--imain={modData}',
                            f'--mask={topupMask}',
                            f'--acqp={self.acqparams_file}',
                            f'--index={indexFile}',
                            f'--bvecs={modBvecs}',
                            f'--bvals={modBvals}',
                            f'--out={wo_repol_outPrefix}',
                            f'--topup={topup_results}',
                            eddy_openmp_params] & FG


                repol_bvecs = np.array(read_bvecs(outPrefix + '.eddy_rotated_bvecs'))
                wo_repol_bvecs = np.array(read_bvecs(wo_repol_outPrefix + '.eddy_rotated_bvecs'))

                merged_bvecs = repol_bvecs.copy()
                merged_bvecs[ind, :] = wo_repol_bvecs[ind, :]

                repol_data = load_nifti(outPrefix + '.nii.gz')
                wo_repol_data = load_nifti(wo_repol_outPrefix + '.nii.gz')
                merged_data = repol_data.get_fdata().copy()
                merged_data[..., ind] = wo_repol_data.get_fdata()[..., ind]

                save_nifti(outPrefix + '.nii.gz', merged_data, repol_data.affine, hdr=repol_data.header)

                # copy bval,bvec to have same prefix as that of eddy corrected volume
                write_bvecs(outPrefix + '.bvec', merged_bvecs)
                copyfile(modBvals, outPrefix + '.bval')
                
                # clean up
                rm['-r', wo_repol_outDir] & FG

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

        primaryMask=[]
        secondaryMask=[]
        if self.b0_brain_mask:
            temp = self.b0_brain_mask.split(',')
            primaryMask = abspath(temp[0])
            if len(temp) == 2:
                secondaryMask = abspath(temp[1])
        


        # obtain 4D/3D info and time axis info
        dimension = load_nifti(primaryVol).header['dim']
        dim1 = dimension[0]
        if dim1!=4:
            raise AttributeError('Primary volume must be 4D, however, secondary can be 3D/4D')
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



        with local.cwd(self.outDir):

            # mask both volumes, fslmaths can do that irrespective of dimension
            logging.info('Masking the volumes')

            primaryMaskedVol = 'primary_masked.nii.gz'
            secondaryMaskedVol = 'secondary_masked.nii.gz'

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
            B0_PA= 'B0_PA.nii.gz'
            B0_AP= 'B0_AP.nii.gz'

            obtainB0(primaryMaskedVol, primaryBval, B0_PA, self.num_b0)

            if dim2==4:
                obtainB0(secondaryMaskedVol, secondaryBval, B0_AP, self.num_b0)
            else:
                B0_AP= secondaryMaskedVol


            B0_PA_AP_merged = 'B0_PA_AP_merged.nii.gz'
            with open(self.acqparams_file._path) as f:
                acqp= f.read().strip().split('\n')
                if len(acqp)!=2:
                    raise ValueError('The acquisition parameter file must have exactly two lines')

            logging.info('Writing acqparams.txt for topup')

            # firstDim: first acqp line should be replicated this number of times
            firstB0dim= load_nifti(str(B0_PA)).header['dim'][4]
            # secondDim: second acqp line should be replicated this number of times
            secondB0dim= load_nifti(str(B0_AP)).header['dim'][4]
            acqp_topup= 'acqp_topup.txt'
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
            # topup --imain=P2A_A2P_b0 --datain=acqparams.txt --config=b02b0.cnf --out=my_output --iout=my_output
            # 
            # === on all b0 images ===
            # https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/TopupUsersGuide#Running_topup
            # topup --imain=all_b0s --datain=acqparams.txt --config=b02b0.cnf --out=my_output --iout=my_output


            logging.info('Running topup')
            topup_results= 'topup_out'
            topupOut= 'topup_out.nii.gz'
            
            # topup --iout yields as many volumes as there are input volumes
            # --iout specifies the name of a 4D image file that contains unwarped and movement corrected images.
            # each volume in the --imain will have a corresponding corrected volume in --iout.

            # --iout is used for creating modified mask only
            # when primary4D,secondary4D/3D are already masked, this will be useful
            topup[f'--imain={B0_PA_AP_merged}',
                  f'--datain={acqp_topup}',
                  f'--out={topup_results}',
                  f'--iout={topupOut}',
                  topup_params.split()] & FG
            
            # provide topupOutMean for quality checking
            topupOutMean= 'topup_out_mean.nii.gz'
            fslmaths[topupOut, '-Tmean', topupOutMean] & FG
            
            
            logging.info('Running applytopup')

            # applytopup always yields one output file regardless of one or two input files
            # if two input files are provided, the resulting undistorted file will be a combination of the two
            # containing only as many volumes as there are in one file
            
            # B0_PA_correct, B0_AP_correct are for quality checking only
            # primaryMaskCorrect, secondaryMaskCorrect will be associated masks
            B0_PA_correct= 'B0_PA_corrected.nii.gz'
            applytopup[f'--imain={B0_PA}',
                       f'--datain={self.acqparams_file}',
                       '--inindex=1',
                       f'--topup={topup_results}',
                       f'--out={B0_PA_correct}',
                       applytopup_params.split()] & FG

            B0_AP_correct= 'B0_AP_corrected.nii.gz'
            applytopup[f'--imain={B0_AP}',
                       f'--datain={self.acqparams_file}',
                       '--inindex=2',
                       f'--topup={topup_results}',
                       f'--out={B0_AP_correct}',
                       applytopup_params.split()] & FG

            B0_PA_AP_corrected_merged= 'B0_PA_AP_corrected_merged'
            fslmerge('-t', B0_PA_AP_corrected_merged, B0_PA_correct, B0_AP_correct)
            fslmaths[B0_PA_AP_corrected_merged, '-Tmean', 'B0_PA_AP_corrected_mean'] & FG


            
            topupMask= 'topup_mask.nii.gz'

            # calculate topup mask
            if primaryMask and secondaryMask:

                fslmaths[primaryMask, '-mul', '1', primaryMask, '-odt', 'float']
                fslmaths[secondaryMask, '-mul', '1', secondaryMask, '-odt', 'float']

                applytopup_params+=' --interp=trilinear'
                
                # this straightforward way could be used
                '''
                applytopup[f'--imain={primaryMask},{secondaryMask}',
                           f'--datain={self.acqparams_file}',
                           '--inindex=1,2',
                           f'--topup={topup_results}',
                           f'--out={topupMask}',
                           applytopup_params.split()] & FG
                '''
                # but let's do it step by step in order to have more control of the process
                


                # binarise the mean of corrected primary,secondary mask to obtain modified mask
                # use that mask for eddy_openmp
                primaryMaskCorrect = 'primary_mask_corrected.nii.gz'
                applytopup[f'--imain={primaryMask}',
                           f'--datain={self.acqparams_file}',
                           '--inindex=1',
                           f'--topup={topup_results}',
                           f'--out={primaryMaskCorrect}',
                           applytopup_params.split()] & FG

                secondaryMaskCorrect = 'secondary_mask_corrected.nii.gz'
                applytopup[f'--imain={secondaryMask}',
                           f'--datain={self.acqparams_file}',
                           '--inindex=2',
                           f'--topup={topup_results}',
                           f'--out={secondaryMaskCorrect}',
                           applytopup_params.split()] & FG

                fslmerge('-t', topupMask, primaryMaskCorrect, secondaryMaskCorrect)
                temp= load_nifti(topupMask)
                data= temp.get_fdata()
                data= abs(data[...,0])+ abs(data[...,1])
                data[data!=0]= 1

                # filter the mask to smooth edges
                # scale num of erosion followed by scale num of dilation
                # the greater the scale, the smoother the edges
                # scale=2 seems sufficient
                data= single_scale(data, int(self.scale))
                save_nifti(topupMask, data.astype('uint8'), temp.affine, temp.header)
                

            else:
                # this block assumes the primary4D,secondary4D/3D are already masked
                # then toupOutMean is also masked
                # binarise the topupOutMean to obtain modified mask
                # use that mask for eddy_openmp
                # fslmaths[topupOutMean, '-bin', topupMask, '-odt', 'char'] & FG

                # if --mask is not provided at all, this block creates a crude mask
                # apply bet on the mean of topup output to obtain modified mask
                # use that mask for eddy_openmp
                bet[topupOutMean, topupMask.split('_mask.nii.gz')[0], '-m', '-n'] & FG
                

                

            logging.info('Writing index.txt for topup')
            indexFile= 'index.txt'
            with open(indexFile, 'w') as f:
                for i in range(numVol1):
                    f.write('1\n')

            

            outPrefix = basename(primaryVol).split('.nii')[0]
            
            # remove _acq- 
            outPrefix= outPrefix.replace('_acq-PA','')
            outPrefix= outPrefix.replace('_acq-AP','')

            # find dir field
            if '_dir-' in primaryVol and '_dir-' in secondaryVol and self.whichVol == '1,2':
                dir= load_nifti(primaryVol).shape[3]+ load_nifti(secondaryVol).shape[3]
                outPrefix= local.path(re.sub('_dir-(.+?)_', f'_dir-{dir}_', outPrefix))


            outPrefix = outPrefix + '_EdEp'
            with open('.outPrefix.txt', 'w') as f:
                f.write(outPrefix)
            


            temp = self.whichVol.split(',')
            if len(temp)==1 and temp[0]=='1':
                # correct only primary4D volume

                _eddy_openmp(primaryMaskedVol, primaryBval, primaryBvec, eddy_openmp_params)


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

                combinedBvals = 'combinedBvals.txt'
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
                combinedBvecs = 'combinedBvecs.txt'
                write_bvecs(combinedBvecs, bvecs1+bvecs2)

                combinedData= 'combinedData.nii.gz'
                fslmerge('-t', combinedData, primaryMaskedVol, secondaryMaskedVol)


                _eddy_openmp(combinedData, combinedBvals, combinedBvecs, eddy_openmp_params)
                

            else:
                raise ValueError('Invalid --whichVol')

            # rename topupMask to have same prefix as that of eddy corrected volume
            move(topupMask, outPrefix + '_mask.nii.gz')



if __name__== '__main__':
    TopupEddyEpi.run()

