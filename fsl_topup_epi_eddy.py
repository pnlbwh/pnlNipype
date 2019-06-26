#!/usr/bin/env python

from plumbum import cli, FG, local
from plumbum.cmd import topup, applytopup, eddy_openmp, fslmaths, rm, fslmerge, cat
from util import BET_THRESHOLD, TemporaryDirectory, logfmt, load_nifti, FILEDIR, \
    topup_params, applytopup_params, eddy_openmp_params
from os.path import join as pjoin, abspath, basename
from subprocess import check_call
from os import environ
from shutil import copyfile
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs
FSLDIR=environ['FSLDIR']

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

# TODO write a tutorial
# ========== fsl_topup_epi_eddy ===========
# --dwi primary4D,secondary4D/3D
# one 4D volume input, can be either AP/PA: primary volume
# mask here
# another 3D/4D volume input, should be opposite (AP/PA) of primary 4D volume
# mask here

# calculate BSE from primary, if secondary is also 4D, estimate BSE from there as well
# introduce --all option with bse

# merge AP_B0 and PA_B0: both_b0 or can be all_b0s

# input my_acq_param.txt with two lines: primary,secondary

# ===========================
# topup --imain=both_b0 --datain=my_acq_param.txt --out=my_topup_results
# topup --imain=all_b0s --datain=written_acqp_param --out=my_topup_results
# ===========================



# ===========================
# applytopup --imain=primaryMask,secondaryMask --inindex=1,2 --datatin=my_acq_param.txt --topup=my_topup_results --out=topupMask
# Here, output is just first volume: how to threshold topupMask then?
# ===========================



# omit the following
# fslmaths my_hifi_b0 -Tmean my_hifi_b0
# bet my_hifi_b0 my_hifi_b0_brain -m


# ===========================
# eddy --imain=primary4Dmasked+secondary4D/3Dmasked --mask=topupMask --acqp=acqparams.txt --index=writtenIndex --bvecs=writtenBvecs --bvals=writtenBvals
#      --topup=my_topup_results --out=eddy_corrected_data
# eddy --imain=primary4Dmasked --mask=topupMask --acqp=acqparams.txt --index=writtenIndex --bvecs=writtenBvecs --bvals=writtenBvals
#      --topup=my_topup_results --out=eddy_corrected_data
# ===========================


# feature:
# introduce config file for each of topup, applytopup, eddy_openmp

def obtainB0(inVol, outVol, num_b0):

    if num_b0 == '1':
        check_call((' ').join([pjoin(FILEDIR,'bse.py'), '-i', inVol, '-o', outVol]), shell=True)
    elif num_b0 == '-1':
        check_call((' ').join([pjoin(FILEDIR,'bse.py'), '-i', inVol, '-o', outVol, '--all']), shell=True)
    else:
        raise ValueError('Invalid --numb0')



class TopupEddyEpi(cli.Application):
    '''Epi and eddy correction using topup and eddy_openmp commands in fsl
    For more info, see:
        https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide
        https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/TopupUsersGuide
    You can also view the help message:
        eddy_openmp
        topup
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
        help='which volume(s) to correct through eddy: 1(only primary4D) or 1,2(primary4D+secondary4D)',
        mandatory=False,
        default=True)


    def main(self):


        temp= self.dwi_file.split(',')
        primaryVol= abspath(temp[0])
        if len(temp)<2:
            raise AttributeError('Two volumes are required for --imain')
        else:
            secondaryVol= abspath(temp[1])


        temp= self.bvals_file.split(',')
        primaryBval= abspath(temp[0])
        if len(temp)==2:
            secondaryBval= abspath(temp[1])
        else:
            secondaryBval=[]

        temp= self.bvecs_file.split(',')
        primaryBvec= abspath(temp[0])
        if len(temp)==2:
            secondaryBvec= abspath(temp[1])
        else:
            secondaryBvec=[]


        with TemporaryDirectory() as tmpdir:

            tmpdir= local.path(tmpdir)

            if not self.b0_brain_mask:
                # create mask for both primary4D and secondary4D/3D
                logging.info('Masks are not provided, creating FSL bet mask for --imain volumes')

                primaryMask = tmpdir / 'primary_mask.nii.gz' # bet should append '_mask.nii.gz'
                secondaryMask = tmpdir / 'secondary_mask.nii.gz' # bet should append '_mask.nii.gz'

                check_call((' ').join([pjoin(FILEDIR, 'bet_mask.py'), '-i', primaryVol, '-o',
                                       primaryMask._path.split('_mask.nii.gz')[0]]), shell=True)

                check_call((' ').join([pjoin(FILEDIR, 'bet_mask.py'), '-i', secondaryVol, '-o',
                                       secondaryMask._path.split('_mask.nii.gz')[0]]), shell=True)

            else:

                temp = self.b0_brain_mask.split(',')
                primaryMask = abspath(temp[0])
                if len(temp) < 2:
                    raise AttributeError('Two masks are required for --mask')
                else:
                    secondaryMask = abspath(temp[1])



            # mask both volumes, fslmaths can do that irrespective of dimension
            logging.info('Masking the volumes')
            primaryMaskedVol= tmpdir / 'primaryMasked.nii.gz'
            secondaryMaskedVol= tmpdir / 'secondaryMasked.nii.gz'
            fslmaths[primaryVol, '-mas', primaryMask, primaryMaskedVol] & FG
            fslmaths[secondaryVol, '-mas', secondaryMask, secondaryMaskedVol] & FG

            # copy bvals so bse.py can extract b0
            copyfile(primaryBval, tmpdir / 'primaryMasked.bval')

            B0_PA= tmpdir / 'B0_PA.nii.gz'
            B0_AP= tmpdir / 'B0_AP.nii.gz'

            logging.info('Extracting B0 from masked volumes')
            obtainB0(primaryMaskedVol, B0_PA, self.num_b0)


            # check if secondary is 4D/3D
            dimension= load_nifti(primaryMaskedVol._path).header['dim']
            dim1=dimension[0]
            numVol1= dimension[4]

            dimension = load_nifti(secondaryMaskedVol._path).header['dim']
            dim2=dimension[0]
            numVol2=dimension[4]

            if dim2==4:
                copyfile(secondaryBval, tmpdir / 'secondaryMasked.bval')
                obtainB0(secondaryMaskedVol, B0_AP, self.num_b0)
            else:
                copyfile(secondaryMaskedVol, B0_AP)


            B0_PA_AP_merged = tmpdir / 'B0_PA_AP_merged.nii.gz'
            with open(self.acqparams_file._path) as f:
                acqp= f.read().split('\n')

            logging.info('Writing acqparams.txt for topup')

            # firstDim: first acqp line should be replicated this number of times
            firstB0dim= load_nifti(B0_PA._path).header['dim'][4]
            # secondDim: second acqp line should be replicated this number of times
            secondB0dim= load_nifti(B0_AP._path).header['dim'][4]
            acqp_topup= tmpdir / 'acqp_topup.txt'
            with open(acqp_topup,'w') as f:
                for i in range(firstB0dim):
                    f.write(acqp[0]+'\n')

                for i in range(secondB0dim):
                    f.write(acqp[1]+'\n')


            logging.info('Merging B0_PA and BO_AP')
            fslmerge('-t', B0_PA_AP_merged, B0_PA, B0_AP)


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
            # applytopup on primary,secondary masks
            topupMask= tmpdir / 'topupMask.nii.gz'
            applytopup[f'--imain={primaryMask},{secondaryMask}',
                       f'--datain={self.acqparams_file}',
                       '--inindex=1,2',
                       f'--topup={topup_results}',
                       f'--out={topupMask}',
                       '--verbose',
                       applytopup_params.split()] & FG


            # threshold maskTmp at 0.5 and obtain modified mask, use that mask for eddy_openmp
            # fslmaths[topupMask, '-thr', '0', topupMask, '-odt' 'char']

            logging.info('Writing index.txt for topup')
            indexFile= tmpdir / 'index.txt'
            with open(indexFile, 'w') as f:
                for i in range(numVol1):
                    f.write('1\n')


            outPrefix = tmpdir / basename(primaryVol).split('.')[0] + '_Ep_Ed'

            temp = self.whichVol.split(',')
            if len(temp)==1 and temp[0]=='1':
                # correct only primary4D volume

                eddy_openmp[f'--imain={primaryMaskedVol}',
                            f'--mask={topupMask}',
                            f'--acqp={self.acqparams_file}',
                            f'--index={indexFile}',
                            f'--bvecs={primaryBvec}',
                            f'--bvals={primaryBval}',
                            f'--out={outPrefix}',
                            f'--topup={topup_results}',
                            '--verbose',
                            eddy_openmp_params.split()] & FG




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
                elif dim2==1:
                    bvals2=[0]

                combinedBvals = tmpdir / 'combinedBvals.txt'
                write_bvals(combinedBvals, bvals1+bvals2)

                # join both bvecFiles
                bvecs1= read_bvecs(primaryBvec)
                if dim2==4 and not secondaryBvec:
                    bvecs2= bvecs1.copy()
                elif dim2==4 and secondaryBvec:
                    bvecs2= read_bvecs(secondaryBvec)
                elif dim2==1:
                    bvecs2=[[0,0,0]]

                # join both bvecFiles
                combinedBvecs = tmpdir / 'combinedBvecs.txt'
                write_bvecs(combinedBvecs, bvecs1+bvecs2)

                combinedData= tmpdir / 'combinedData.nii.gz'
                fslmerge('-t', combinedData, primaryMaskedVol, secondaryMaskedVol)

                eddy_openmp[f'--imain={combinedData}',
                            f'--mask={topupMask}',
                            f'--acqp={self.acqparams_file}',
                            f'--index={indexFile}',
                            f'--bvecs={combinedBvecs}',
                            f'--bvals={combinedBvals}',
                            f'--out={outPrefix}',
                            f'--topup={topup_results}',
                            '--verbose',
                            eddy_openmp_params.split()] & FG


            else:
                raise ValueError('Invalid --whichVol')


            # copy bval,bvec to have same prefix as that of eddy corrected volume
            copyfile(outPrefix+'.eddy_rotated_bvecs', outPrefix+'.bvec')
            copyfile(primaryBval, outPrefix+'.bval')

            tmpdir.move(self.outDir)


if __name__== '__main__':
    TopupEddyEpi.run()
