#!/usr/bin/env python

from plumbum.cmd import bet, fslroi
from plumbum import cli, FG, local
import os
import numpy as np
from bvec_rotation import read_bvals


class App(cli.Application):
    """Extracts the brain mask of a 3D of 4D nifti image using fsl bet tool"""

    img = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='input 3D or 4D nifti image',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--out'],
        help='''prefix for output brain mask (default: input prefix).
             output file is named as prefix_mask.nii.gz''',
        mandatory=False)

    bet_threshold = cli.SwitchAttr(
        '-f',
        help= 'threshold for fsl bet mask',
        mandatory=False,
        default= 0.25)

    def main(self):

        prefix= self.img.name.split('.')[0]
        directory= self.img.parent

        if self.out is None:
            self.out= os.path.join(directory, prefix)

        # bet changed in FSL 6.0.1, it creates a mask for every volume in 4D
        # if the image is 4D, baseline image should be extracted first

        bval_file = os.path.join(directory, prefix + '.bval')
        bvals = read_bvals(bval_file)
        idx = np.where([bval < 50 for bval in bvals])[0]

        with local.tempdir() as tmpdir:
            bsetmp= tmpdir / 'bse.nii.gz'

            if len(idx) >= 1:
                fslroi[self.img, bsetmp, idx, 1] & FG

                bet[bsetmp, self.out, '-m', '-f', self.bet_threshold] & FG

            else:
                raise Exception('No b0 image found. Check the bval file.')

if __name__ == '__main__':
    App.run()