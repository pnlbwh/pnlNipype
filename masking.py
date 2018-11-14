#!/usr/bin/env python

from plumbum.cmd import ImageMath
from plumbum import cli

class App(cli.Application):
    "Multiplies an image by its mask"

    mask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='nifti mask, 3D image',
        mandatory=True)

    img = cli.SwitchAttr(
        ['-i', '--infile'],
        cli.ExistingFile,
        help='nifti image, 3D or 4D image',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--outfile'],
        help= 'Extracted baseline image (default: input_prefix_bse.nii.gz)',
        mandatory=True)

    dim= cli.SwitchAttr(
        ['-d', '--dimension'],
        help= 'Input image dimension: 3D or 4D',
        mandatory=True)

    def main(self):


        ImageMath(self.dim, self.out, 'm', self.img, self.mask)



if __name__ == '__main__':
    App.run()