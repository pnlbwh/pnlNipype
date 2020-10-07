#!/usr/bin/env python

from __future__ import print_function
from os import getpid
from plumbum import local, cli
from plumbum.cmd import antsApplyTransforms, antsRegistration, fslmaths, WarpTimeSeriesImageMultiTransform
from fs2dwi import rigid_registration
from subprocess import check_call
from util import logfmt, TemporaryDirectory, FILEDIR, pjoin, N_PROC
import sys

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    'Epi distortion correction.'


    debug = cli.Flag(
            ['-d', '--debug'],
            help='Debug, save intermediate files in \'epidebug-<pid>\'')

    force = cli.Flag(
            '--force',
            help='Force overwrite if output already exists')

    dwi = cli.SwitchAttr(
            '--dwi',
            cli.ExistingFile,
            help='DWI',
            mandatory=True)

    bse = cli.SwitchAttr(
        '--bse',
        cli.ExistingFile,
        help='b0 of the DWI',
        mandatory=False)

    bvecs_file= cli.SwitchAttr(
        ['--bvecs'],
        cli.ExistingFile,
        help='bvecs file of the DWI',
        mandatory=True)

    bvals_file= cli.SwitchAttr(
        ['--bvals'],
        cli.ExistingFile,
        help='bvals file of the DWI',
        mandatory=True)

    dwimask = cli.SwitchAttr(
            '--dwimask',
            cli.ExistingFile,
            help='DWI mask',
            mandatory=True)

    t2 = cli.SwitchAttr(
            '--t2',
            cli.ExistingFile,
            help='T2w',
            mandatory=True)

    t2mask = cli.SwitchAttr(
            '--t2mask',
            cli.ExistingFile,
            help='T2w mask',
            mandatory=True)

    out = cli.SwitchAttr(
            ['-o', '--output'],
            help='Prefix for EPI corrected DWI, same prefix is used for saving bval, bvec, and mask',
            mandatory=True)

    nproc = cli.SwitchAttr(
            ['-n', '--nproc'], help='''number of threads to use, if other processes in your computer 
            becomes sluggish/you run into memory error, reduce --nproc''', default= N_PROC)

    def main(self):

        self.out = local.path(self.out)
        if not self.force and self.out.exists():
            logging.error('{} already exists, use --force to force overwrite.'.format(self.out))
            sys.exit(1)


        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            bse = tmpdir / 'maskedbse.nii.gz'
            t2masked = tmpdir / 'maskedt2.nii.gz'
            t2inbse = tmpdir / 't2inbse.nii.gz'
            epiwarp = tmpdir / 'epiwarp.nii.gz'

            t2tobse_rigid = tmpdir / 't2tobse_rigid'
            affine= tmpdir / 't2tobse_rigid0GenericAffine.mat'

            logging.info('1. Extract B0 and and mask it')
            if not self.bse:
                check_call((' ').join([pjoin(FILEDIR, 'bse.py'), '-m', self.dwimask, '-i', self.dwi, 
                                       '--bvals', self.bvals_file, '-o', bse]), shell=True)
            else:
                self.bse.copy(bse)

            logging.info('2. Mask the T2')
            fslmaths(self.t2mask, '-mul', self.t2, t2masked)

            logging.info('3. Compute a rigid registration from the T2 to the DWI baseline')
            rigid_registration(3, t2masked, bse, t2tobse_rigid)

            antsApplyTransforms('-d', '3', '-i', t2masked, '-o', t2inbse, '-r', bse, '-t', affine)


            logging.info('4. Compute 1d nonlinear registration from the DWI to T2-in-bse along the phase direction')
            moving = bse
            fixed = t2inbse
            pre = tmpdir / 'epi'
            dwiepi = tmpdir / 'dwiepi.nii.gz'
            antsRegistration('-d', '3', '-m',
                             'cc[' + str(fixed) + ',' + str(moving) + ',1,2]', '-t',
                             'SyN[0.25,3,0]', '-c', '50x50x10', '-f', '4x2x1',
                             '-s', '2x1x0', '--restrict-deformation', '0x1x0',
                             '-v', '1', '-o', pre)

            local.path(str(pre) + '0Warp.nii.gz').move(epiwarp)

            logging.info('5. Apply warp to the DWI')
            check_call((' ').join([pjoin(FILEDIR, 'antsApplyTransformsDWI.py'), '-i', self.dwi, '-m', self.dwimask,
                                  '-t', epiwarp, '-o', dwiepi, '-n', self.nproc]), shell= True)


            # WarpTimeSeriesImageMultiTransform can also be used
            # dwimasked = tmpdir / 'masked_dwi.nii.gz'
            # fslmaths(self.dwi, '-mul', self.dwimask, dwimasked)
            # WarpTimeSeriesImageMultiTransform('4', dwimasked, dwiepi, '-R', dwimasked, '-i', epiwarp)

            logging.info('6. Apply warp to the DWI mask')
            epimask = self.out._path+'_mask.nii.gz'
            antsApplyTransforms('-d', '3', '-i', self.dwimask, '-o', epimask,
                                '-n', 'NearestNeighbor', '-r', bse, '-t', epiwarp)
            fslmaths(epimask, '-mul', '1', epimask, '-odt', 'char')


            dwiepi.move(self.out._path+'.nii.gz')
            self.bvals_file.copy(self.out._path+'.bval')
            self.bvecs_file.copy(self.out._path+'.bvec')


            if self.debug:
                tmpdir.copy(self.out.dirname / ('epi-debug-' + str(getpid())))


if __name__ == '__main__':
    App.run()
