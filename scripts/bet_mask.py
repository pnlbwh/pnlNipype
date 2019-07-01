#!/usr/bin/env python

from plumbum.cmd import bet, fslroi
from plumbum import cli, FG, local
import os
import numpy as np
from conversion import read_bvals
from util import BET_THRESHOLD, B0_THRESHOLD, load_nifti


def bet_mask(imgPath, maskPath, dim, bvalFile= None, thr= BET_THRESHOLD):

    with local.tempdir() as tmpdir:
        bsetmp = tmpdir / 'bse.nii.gz'

        if dim==4:
            bvals = read_bvals(bvalFile)
            idx = np.where([bval < B0_THRESHOLD for bval in bvals])[0]


            if len(idx) >= 1:
                fslroi[imgPath, bsetmp, idx, 1] & FG

                bet[bsetmp, maskPath, '-m', '-n', '-f', thr] & FG

            else:
                raise Exception('No b0 image found. Check the bval file.')


        elif dim==3:
            bet[imgPath, maskPath, '-m', '-n', '-f', thr] & FG


        else:
            raise ValueError('Input dimension should be 3 or 4')


class App(cli.Application):
    """Extracts the brain mask of a 3D/4D nifti image using fsl bet command"""

    img = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='input 3D/4D nifti image',
        mandatory=True)

    bval_file = cli.SwitchAttr(
        '--bvals',
        cli.ExistingFile,
        help='bval file for 4D DWI, default: inputPrefix.bval')

    out = cli.SwitchAttr(
        ['-o', '--outPrefix'],
        help='prefix for output brain mask (default: input prefix), output file is named as prefix_mask.nii.gz',
        mandatory=False)

    bet_threshold = cli.SwitchAttr(
        '-f',
        help= 'threshold for fsl bet mask',
        mandatory=False,
        default= BET_THRESHOLD)


    def main(self):

        prefix= self.img.name.split('.')[0]
        directory= self.img.parent

        if self.out is None:
            self.out= os.path.join(directory, prefix)

        # bet changed in FSL 6.0.1, it creates a mask for every volume in 4D
        # if the image is 4D, baseline image should be extracted first

        dim= load_nifti(self.img._path).header['dim'][0]

        if dim==4:
            if not self.bval_file:
                self.bval_file = os.path.join(directory, prefix + '.bval')

            bet_mask(self.img._path, self.out, 4, self.bval_file, thr= self.bet_threshold)

        else:
            bet_mask(self.img._path, self.out, 3, thr= self.bet_threshold)




if __name__ == '__main__':
    App.run()
