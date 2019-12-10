#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory
from plumbum import local, cli, FG
from plumbum.cmd import WarpImageMultiTransform, fslsplit, fslmaths, fslmerge

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))
from multiprocessing import Pool


def _WarpImage(dwimask, vol, xfm):

    if dwimask:
        fslmaths[vol, '-mas', dwimask, vol]

    volwarped = vol.stem + '-warped.nii.gz'
    WarpImageMultiTransform('3', vol, volwarped, '-R', vol, xfm)

    return volwarped


class App(cli.Application):
    """Applies a transformation to a DWI nrrd, with option of masking first.
    (Used by epi.py)"""

    debug = cli.Flag(
        ['-d', '--debug'], help='debug, makes antsApplyTransformsDWi-<pid>')
    dwi = cli.SwitchAttr(
        ['-i', '--inpur'], cli.ExistingFile, help='DWI in nifti', mandatory=True)
    dwimask = cli.SwitchAttr(
        ['--dwimask', '-m'], cli.ExistingFile, help='DWI mask in nifti', mandatory=False)
    xfm = cli.SwitchAttr(['--transform', '-t'], cli.ExistingFile, help='transform', mandatory=True)
    out = cli.SwitchAttr(['-o', '--output'], cli.NonexistentPath, help='transformed DWI')
    nproc = cli.SwitchAttr(
        ['-n', '--nproc'], help='''number of threads to use, if other processes in your computer 
        becomes sluggish/you run into memory error, reduce --nproc''', default= 8)

    def main(self):
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
            tmpdir = local.path(tmpdir)
            dicePrefix = 'vol'

            logging.info("Dice DWI")
            fslsplit[self.dwi] & FG

            logging.info("Apply warp to each DWI volume")
            vols = sorted(tmpdir // (dicePrefix + '*.nii.gz'))

            # use the following multi-processed loop
            pool= Pool(int(self.nproc))
            res= []
            for vol in vols:
                res.append(pool.apply_async(_WarpImage, (self.dwimask, vol, self.xfm)))

            volsWarped= [r.get() for r in res]
            pool.close()
            pool.join()


            # or use the following for loop
            # volsWarped = []
            # for vol in vols:
            #     if self.dwimask:
            #         fslmaths[vol, '-mas', self.dwimask, vol]
            #     volwarped = vol.stem + '-warped.nii.gz'
            #     WarpImageMultiTransform('3', vol, volwarped, '-R', vol, self.xfm)
            #     volsWarped.append(volwarped)

            logging.info("Join warped volumes together")

            volsWarped.sort()
            fslmerge['-t', self.out, volsWarped] & FG


            logging.info('Made ' + str(self.out))

            if self.debug:
                from os import getpid
                pid = str(getpid())
                d = local.path(self.out.dirname /
                               ('antsApplyTransformsDWi-' + pid))
                tmpdir.copy(d)


if __name__ == '__main__':
    App.run()
