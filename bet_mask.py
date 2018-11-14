#!/usr/bin/env python

from plumbum.cmd import bet
from plumbum import cli, FG
import os


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


        bet[self.img, self.out, '-m', '-f', self.bet_threshold] & FG


if __name__ == '__main__':
    App.run()