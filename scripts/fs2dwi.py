#!/usr/bin/env python

from plumbum import local, cli
import sys, os, tempfile, psutil, warnings
from plumbum.cmd import ResampleImageBySpacing, antsApplyTransforms, ImageMath
from subprocess import check_call

from util import load_nifti, FILEDIR, pjoin


def rigid_registration(dim, moving, fixed, outPrefix):

    check_call((' ').join([pjoin(FILEDIR,'antsRegistrationSyNMI.sh'), '-d', str(dim), '-t', 'r', '-m', moving, 
                           '-f', fixed, '-o', outPrefix]), shell=True)


def registerFs2Dwi(tmpdir, namePrefix, b0masked, brain, wmparc, wmparc_out):

    pre = tmpdir / namePrefix
    affine = pre + '0GenericAffine.mat'
    warp = pre + '1Warp.nii.gz'

    print('Computing warp from brain.nii.gz to (resampled) baseline')
    check_call((' ').join([pjoin(FILEDIR,'antsRegistrationSyNMI.sh'), '-d', '3', '-m', brain, '-f', b0masked, '-o', pre
                           ]), shell=True)

    print('Applying warp to wmparc.nii.gz to create (resampled) wmparcindwi.nii.gz')
    antsApplyTransforms('-d', '3', '-i', wmparc, '-t', warp, affine,
                        '-r', b0masked, '-o', wmparc_out,
                        '--interpolation', 'NearestNeighbor')

    print('Made ' + wmparc_out)


# The functions registerFs2Dwi and registerFs2Dwi_T2 differ by the use of t2masked, T2toBrainAffine, and a print statement


def registerFs2Dwi_T2(tmpdir, namePrefix, b0masked, t2masked, BrainToT2Affine, wmparc, wmparc_out):

    pre = tmpdir / namePrefix
    affine = pre + '0GenericAffine.mat'
    warp = pre + '1Warp.nii.gz'

    print('Computing warp from t2 to (resampled) baseline')
    check_call((' ').join([pjoin(FILEDIR,'antsRegistrationSyNMI.sh'), '-d', '3', '-m', t2masked, '-f', b0masked, '-o', pre
                           ]), shell=True)

    print('Applying warp to wmparc.nii.gz to create (resampled) wmparcindwi.nii.gz')
    antsApplyTransforms('-d', '3', '-i', wmparc, '-t', warp, affine, BrainToT2Affine,
                        '-r', b0masked, '-o', wmparc_out,
                        '--interpolation', 'NearestNeighbor')

    print('Made ' + wmparc_out)


class FsToDwi(cli.Application):
    """Registers Freesurfer labelmap to DWI space."""

    fsdir = cli.SwitchAttr(
        ['-f', '--freesurfer'],
        cli.ExistingDirectory,
        help='freesurfer subject directory',
        mandatory=True)

    dwi = cli.SwitchAttr(
        ['--dwi'],
        cli.ExistingFile,
        help='target DWI')
    
    bvals_file= cli.SwitchAttr(
        ['--bvals'],
        cli.ExistingFile,
        help='bvals file of the DWI')

    bse = cli.SwitchAttr(
        ['--bse'],
        cli.ExistingFile,
        help='masked bse of DWI')

    dwimask = cli.SwitchAttr(
        ['--dwimask'],
        cli.ExistingFile,
        help='DWI mask',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--outDir'],
        help='output directory',
        mandatory=True)

    force= cli.Flag(
        ['--force'],
        help='turn on this flag to overwrite existing output',
        default= False)

    debug = cli.Flag(
        ['-d','--debug'],
        help='Debug mode, saves intermediate transforms to out/fs2dwi-debug-<pid>',
        default= False)

    def main(self):

        if not self.nested_command:
            print("No command given")
            sys.exit(1)

        self.fshome = local.path(os.getenv('FREESURFER_HOME'))

        if not self.fshome:
            print('Set FREESURFER_HOME first.')
            sys.exit(1)

        if not (self.bse or self.bvals_file):
            print('--bvals file is required for extracting B0')
            sys.exit(1)

        print('Making output directory')
        self.out= local.path(self.out)
        if self.out.exists() and self.force:
            print('Deleting existing directory')
            self.out.delete()
        self.out.mkdir()


@FsToDwi.subcommand("direct")
class Direct(cli.Application):
    """Direct registration from Freesurfer to B0."""

    def main(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            tmpdir = local.path(tmpdir)

            b0masked = tmpdir / "b0masked.nii.gz" # Sylvain wants both
            b0maskedbrain = tmpdir / "b0maskedbrain.nii.gz"

            brain = tmpdir / "brain.nii.gz"
            wmparc = tmpdir / "wmparc.nii.gz"

            brainmgz = self.parent.fsdir / 'mri/brain.mgz'
            wmparcmgz = self.parent.fsdir / 'mri/wmparc.mgz'

            wmparcindwi = tmpdir / 'wmparcInDwi.nii.gz' # Sylvain wants both
            wmparcinbrain = tmpdir / 'wmparcInBrain.nii.gz'

            print("Making brain.nii.gz and wmparc.nii.gz from their mgz versions")

            vol2vol = local[self.parent.fshome / 'bin/mri_vol2vol']
            label2vol = local[self.parent.fshome / 'bin/mri_label2vol']

            with local.env(SUBJECTS_DIR=''):
                vol2vol('--mov', brainmgz, '--targ', brainmgz, '--regheader',
                        '--o', brain)
                label2vol('--seg', wmparcmgz, '--temp', brainmgz,
                          '--regheader', wmparcmgz, '--o', wmparc)

            if not self.parent.bse:
                print('Extracting B0 from DWI and masking it')
                check_call((' ').join([pjoin(FILEDIR, 'bse.py'), '-i', self.parent.dwi, '--bvals', self.parent.bvals_file,
                                       '-m', self.parent.dwimask, '-o', b0masked]), shell= True)
                print('Made masked B0')
            else:
                self.parent.bse.copy(b0masked)


            dwi_res= load_nifti(str(b0masked)).header['pixdim'][1:4].round(decimals=2)
            brain_res= load_nifti(str(brain)).header['pixdim'][1:4].round(decimals=2)
            print(f'DWI resolution: {dwi_res}')
            print(f'FreeSurfer brain resolution: {brain_res}')


            print('Registering wmparc to B0')
            registerFs2Dwi(tmpdir, 'fsbrainToB0', b0masked, brain, wmparc, wmparcindwi)

            if (dwi_res!=brain_res).any():
                print('DWI resolution is different from FreeSurfer brain resolution')
                print('wmparc wil be registered to both DWI and brain resolution')
                print('Check output files wmparcInDwi.nii.gz and wmparcInBrain.nii.gz')

                print('Resampling B0 to brain resolution')

                ResampleImageBySpacing('3', b0masked, b0maskedbrain, brain_res.tolist())

                print('Registering wmparc to resampled B0')
                registerFs2Dwi(tmpdir, 'fsbrainToResampledB0', b0maskedbrain, brain, wmparc, wmparcinbrain)


            # copying images to outDir
            b0masked.copy(self.parent.out)
            wmparcindwi.copy(self.parent.out)

            if b0maskedbrain.exists():
                b0maskedbrain.copy(self.parent.out)
                wmparcinbrain.copy(self.parent.out)

            if self.parent.debug:
                tmpdir.copy(self.parent.out, 'fs2dwi-debug-' + str(os.getpid()))


        print('See output files in ', self.parent.out._path)

@FsToDwi.subcommand("witht2")
class WithT2(cli.Application):
    """Registration from Freesurfer to T2 to B0."""

    t2 = cli.SwitchAttr(
        ['--t2'],
        cli.ExistingFile,
        help='T2 image',
        mandatory=True)

    t2mask = cli.SwitchAttr(
        ['--t2mask'],
        cli.ExistingFile,
        help='T2 mask',
        mandatory=True)


    def main(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            tmpdir = local.path(tmpdir)

            b0masked = tmpdir / "b0masked.nii.gz" # Sylvain wants both
            b0maskedbrain = tmpdir / "b0maskedbrain.nii.gz"

            t2masked= tmpdir / 't2masked.nii.gz'
            print('Masking the T2')
            ImageMath(3, t2masked, 'm', self.t2, self.t2mask)

            brain = tmpdir / "brain.nii.gz"
            wmparc = tmpdir / "wmparc.nii.gz"

            brainmgz = self.parent.fsdir / 'mri/brain.mgz'
            wmparcmgz = self.parent.fsdir / 'mri/wmparc.mgz'

            wmparcindwi = tmpdir / 'wmparcInDwi.nii.gz' # Sylvain wants both
            wmparcinbrain = tmpdir / 'wmparcInBrain.nii.gz'

            print("Making brain.nii.gz and wmparc.nii.gz from their mgz versions")

            vol2vol = local[self.parent.fshome / 'bin/mri_vol2vol']
            label2vol = local[self.parent.fshome / 'bin/mri_label2vol']

            with local.env(SUBJECTS_DIR=''):
                vol2vol('--mov', brainmgz, '--targ', brainmgz, '--regheader',
                        '--o', brain)
                label2vol('--seg', wmparcmgz, '--temp', brainmgz,
                          '--regheader', wmparcmgz, '--o', wmparc)

            if not self.parent.bse:
                print('Extracting B0 from DWI and masking it')
                check_call((' ').join([pjoin(FILEDIR, 'bse.py'), '-i', self.parent.dwi, '--bvals', self.parent.bvals_file,
                                       '-m', self.parent.dwimask, '-o', b0masked]), shell= True)
                print('Made masked B0')
            else:
                self.parent.bse.copy(b0masked)


            # rigid registration from brain.nii.gz to t2
            pre = tmpdir / 'BrainToT2'
            BrainToT2Affine = pre + '0GenericAffine.mat'

            print('Computing rigid registration from brain.nii.gz to t2')
            rigid_registration(3, brain, t2masked, pre)
            # generates three files for rigid registration:
            # pre0GenericAffine.mat  preInverseWarped.nii.gz  preWarped.nii.gz

            # generates five files for default(rigid+affine+deformable syn) registration:
            # pre0GenericAffine.mat  pre1Warp.nii.gz  preWarped.nii.gz   pre1InverseWarp.nii.gz  preInverseWarped.nii.gz


            dwi_res= load_nifti(str(b0masked)).header['pixdim'][1:4].round(decimals=2)
            brain_res= load_nifti(str(brain)).header['pixdim'][1:4].round(decimals=2)
            print(f'DWI resolution: {dwi_res}')
            print(f'FreeSurfer brain resolution: {brain_res}')


            print('Registering wmparc to B0 through T2')
            registerFs2Dwi_T2(tmpdir, 'fsbrainToT2ToB0', b0masked, t2masked,
                              BrainToT2Affine, wmparc, wmparcindwi)

            if (dwi_res!=brain_res).any():
                print('DWI resolution is different from FreeSurfer brain resolution')
                print('wmparc wil be registered to both DWI and brain resolution')
                print('Check output files wmparcInDwi.nii.gz and wmparcInBrain.nii.gz')

                print('Resampling B0 to brain resolution')

                ResampleImageBySpacing('3', b0masked, b0maskedbrain, brain_res.tolist())

                print('Registering wmparc to resampled B0')
                registerFs2Dwi_T2(tmpdir, 'fsbrainToT2ToResampledB0', b0maskedbrain, t2masked,
                                  BrainToT2Affine, wmparc, wmparcinbrain)

            # copying images to outDir
            b0masked.copy(self.parent.out)
            wmparcindwi.copy(self.parent.out)

            if b0maskedbrain.exists():
                b0maskedbrain.copy(self.parent.out)
                wmparcinbrain.copy(self.parent.out)

            if self.parent.debug:
                tmpdir.copy(self.parent.out, 'fs2dwi-debug-' + str(os.getpid()))


        print('See output files in ', self.parent.out._path)

if __name__ == '__main__':
    FsToDwi.run()
