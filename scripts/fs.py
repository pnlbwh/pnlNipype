#!/usr/bin/env python

from __future__ import print_function
from util import logfmt, TemporaryDirectory, N_CPU, __version__, FILEDIR, pjoin
from plumbum import local, cli, FG
from plumbum.cmd import ImageMath, recon_all
from subprocess import Popen
import sys
import os


import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Convenient script to run Freesurfer segmentation"""

    VERSION = __version__

    t1 = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='t1 image in nifti format (nii, nii.gz)',
        mandatory=True)

    t1mask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='mask the t1 before running Freesurfer; if not provided, -skullstrip is enabled with Freesurfer segmentation',
        mandatory=False)

    t2 = cli.SwitchAttr(
        ['--t2'],
        cli.ExistingFile,
        help='t2 image in nifti format (nii, nii.gz)',
        mandatory=False)

    t2mask = cli.SwitchAttr(
        ['--t2mask'],
        cli.ExistingFile,
        help='mask the t2 before running Freesurfer, if t2 is provided but not its mask, -skullstrip is enabled with Freesurfer segmentation',
        mandatory=False)

    force = cli.Flag(
        ['-f', '--force'],
        help='if --force is used, any previous output will be overwritten')

    out = cli.SwitchAttr(
        ['-o', '--outDir'],
        help='output directory',
        mandatory=True)

    ncpu = cli.SwitchAttr(['-n', '--nproc'],
        help='number of processes/threads to use (-1 for all available) for Freesurfer segmentation',
        default= 1)
        
    expert_file = cli.SwitchAttr(['--expert'],
        cli.ExistingFile,
        help='expert options to use with recon-all for high-resolution data, see https://surfer.nmr.mgh.harvard.edu/fswiki/SubmillimeterRecon',
        default= pjoin(FILEDIR, 'expert_file.txt'))
        
    no_hires = cli.Flag(
        ['--nohires'],
        help= 'omit high resolution freesurfer segmentation i.e. do not use -hires flag')

    no_skullstrip = cli.Flag(
        ['--noskullstrip'],
        help= 'if you do not provide --mask but --input is already masked, omit further skull stripping by freesurfer')
    
    subfields = cli.Flag(
        ['--subfields'],
        help= 'FreeSurfer 7 supported -subfields')

    no_rand = cli.Flag(
        ['--norandomness'],
        help= 'use the same random seed for certain binaries run under recon-all')


    def main(self):
        fshome = local.path(os.getenv('FREESURFER_HOME'))

        if not fshome:
            logging.error('Set FREESURFER_HOME first.')
            sys.exit(1)

        if not self.force and os.path.exists(self.out):
            logging.error(
                'Output directory exists, use -f/--force to force an overwrite.')
            sys.exit(1)
        
        if self.t2mask and not self.t2:
            raise AttributeError('--t2mask is invalid without --t2')
        

        with TemporaryDirectory() as tmpdir, local.env(SUBJECTS_DIR=tmpdir, FSFAST_HOME='', MNI_DIR=''):
            
            tmpdir = local.path(tmpdir)

            if self.t1mask:
                logging.info('Mask the t1')
                t1 = tmpdir / 't1masked.nii.gz'
                ImageMath('3', t1, 'm', self.t1, self.t1mask)

            else:
                t1 = tmpdir / 't1.nii.gz'
                self.t1.copy(t1)
            
            subjid = self.t1.stem
            common_params=['-s', subjid]


            autorecon3_params=[]
            if self.t2:
                if self.t2mask:
                    logging.info('Mask the t2')
                    t2 = tmpdir / 't2masked.nii.gz'
                    ImageMath('3', t2, 'm', self.t2, self.t2mask)
            
                else:
                    t2 = tmpdir / 't2.nii.gz'
                    self.t2.copy(t2)  
                
                autorecon3_params= ['-T2', t2, '-T2pial']
            
            if self.subfields:
                autorecon3_params+=['-subfields']

            logging.info("Running freesurfer on " + t1)

            if self.ncpu=='-1':
                self.ncpu= str(N_CPU)

            if int(self.ncpu)>1:
                common_params+=['-parallel', '-openmp', self.ncpu]

            autorecon1_params=[]
            if not self.no_hires:
                common_params.append('-hires')
                autorecon1_params=['-expert', self.expert_file]

            if self.no_rand:
                common_params.append('-norandomness')


            # run recon_all in three steps so we can overwrite/provide MABS masked T1
            # -noskullstrip is used with -autorecon1 only, so we need to check whether T1 is masked/T1 mask is provided
            # irrespective of masked/unmasked T2
            if self.t1mask or self.no_skullstrip:
                recon_all['-i', t1, common_params, '-autorecon1', autorecon1_params, '-noskullstrip'] & FG
                (tmpdir / subjid / 'mri/T1.mgz').copy(tmpdir / subjid / 'mri/brainmask.mgz')
            else:
                recon_all['-i', t1, common_params, '-autorecon1', autorecon1_params] & FG

            recon_all[common_params, '-autorecon2'] & FG
            recon_all[common_params, '-autorecon3', autorecon3_params] & FG

            
            logging.info("Freesurfer done.")

            (tmpdir / subjid).copy(self.out, override=True)  # overwrites any existing directory
            logging.info("Made " + self.out)


if __name__ == '__main__':
    App.run()
