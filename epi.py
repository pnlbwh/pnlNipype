#!/usr/bin/env python

from __future__ import print_function
from os import getpid
from plumbum import local, cli
from plumbum.cmd import antsApplyTransforms, antsRegistration, fslmaths, WarpTimeSeriesImageMultiTransform, ImageMath
import sys, tempfile
from subprocess import check_call
from fs2dwi_t2 import rigid_registration


def logfmt(scriptname):
    return '%(asctime)s ' + scriptname + ' %(levelname)s  %(message)s'

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):

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
            ['-o', '--out'],
            help='EPI corrected DWI',
            mandatory=True)

    def main(self):

        if not self.force and self.out.exists():
            logging.error('{} already exists, use --force to overwrite.'.format(self.out))
            sys.exit(1)

        self.out= local.path(self.out)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            bse = tmpdir / 'maskedbse.nii.gz'
            t2masked = tmpdir / 'maskedt2.nii.gz'
            dwimasked= tmpdir / 'masked_dwi.nii.gz'
            t2inbse = tmpdir / 't2inbse.nii.gz'
            epiwarp = tmpdir / 'epiwarp.nii.gz'

            t2tobse_rigid = tmpdir / 't2tobse_rigid'
            affine= tmpdir / 't2tobse_rigid0GenericAffine.mat'


            logging.info('1. Extract and mask the DWI b0')
            check_call((' ').join(['bse.py', '-m', self.dwimask, '-i', self.dwi, '-o', bse]), shell= True)

            logging.info('2. Mask the T2')
            ImageMath(3, t2masked, 'm', self.t2, self.t2mask)
            # fslmaths(self.t2mask, '-mul', self.t2, t2masked)

            logging.info('3. Compute a rigid registration from the T2 to the DWI baseline')
            rigid_registration(3, t2masked, bse, t2tobse_rigid)

            antsApplyTransforms('-d', '3', '-i', t2masked, '-o', t2inbse, '-r', bse,
                                '-t', affine)

            logging.info(
                '4. Compute 1d nonlinear registration from the DWI to the T2 along the phase direction')
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
            fslmaths(self.dwi, '-mul', self.dwimask, dwimasked)
            WarpTimeSeriesImageMultiTransform('4', dwimasked, dwiepi, '-R', dwimasked, epiwarp)


            dwiepi.move(self.out)

            if self.debug:
                tmpdir.copy(self.out.dirname / ('epidebug-' + str(getpid())))


if __name__ == '__main__':
    App.run()

'''

~/Downloads/Dummy-PNL-nipype/epi.py \
--dwimask /home/tb571/Downloads/INTRuST/003_GNX_007/raw/003_GNX_007-dwi_mask.nii.gz \
--dwi /home/tb571/Downloads/INTRuST/003_GNX_007/raw/003_GNX_007-dwi.nii.gz \
-o /home/tb571/Downloads/INTRuST/003_GNX_007/raw/epi_corrected.nii.gz \
--force \
--t2 /home/tb571/Downloads/INTRuST/003_GNX_007/raw/003_GNX_007-t2w.nhdr \
--t2mask /home/tb571/Downloads/INTRuST/003_GNX_007/raw/003_GNX_007-t2w-raw-mask.nrrd

'''
