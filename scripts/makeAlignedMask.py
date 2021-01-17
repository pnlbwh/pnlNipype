#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory, FILEDIR, pjoin
from plumbum import local, cli, FG
from plumbum.cmd import antsApplyTransforms
from subprocess import check_call

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Align a given labelmap (usually a mask) to make another labelmap"""

    infile = cli.SwitchAttr(['-i','--input'],
                            cli.ExistingFile, help='structural (nrrd/nii)',mandatory=True)

    labelmap = cli.SwitchAttr(['-l','--labelmap'],
                              cli.ExistingFile, help='structural labelmap, usually a mask (nrrd/nii)',mandatory=True)

    target = cli.SwitchAttr(['-t','--target'],
                            cli.ExistingFile, help='target image (nrrd/nii)',mandatory=True)

    out = cli.SwitchAttr(['-o', '--output'], help='output labelmap (nrrd/nii)',mandatory=True)

    reg_method= cli.SwitchAttr(['--reg'], cli.Set('rigid','SyN', case_sensitive=False),
                               help='ANTs registration method: rigid or SyN', default='rigid')

    def main(self):
        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            pre = tmpdir / 'ants'

            warp = pre + '1Warp.nii.gz'
            affine = pre + '0GenericAffine.mat'

            check_call((' ').join([pjoin(FILEDIR,'antsRegistrationSyNMI.sh'),
                        '-f', self.target,
                        '-m', self.infile,
                        '-t r' if self.reg_method=='rigid' else '',
                        '-o', pre
                        ]), shell= True)

            xfrms= f'-t {warp} -t {affine}' if self.reg_method=='SyN' else f'-t {affine}'

            antsApplyTransforms['-d', '3'
                                ,'-i', self.labelmap
                                ,xfrms.split()
                                ,'-r', self.target
                                ,'-o', self.out
                                ,'--interpolation', 'NearestNeighbor'] & FG

if __name__ == '__main__':
    App.run()
