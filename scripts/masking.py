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
        ['-i', '--input'],
        cli.ExistingFile,
        help='nifti image, 3D/4D image',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--output'],
        help= 'Masked input image',
        mandatory=True)

    dim= cli.SwitchAttr(
        ['-d', '--dimension'],
        help= 'Input image dimension: 3/4',
        mandatory=True)

    def main(self):

        ImageMath(self.dim, self.out, 'm', self.img, self.mask)


if __name__ == '__main__':
    App.run()
