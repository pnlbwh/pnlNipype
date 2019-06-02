#!/usr/bin/env python

from plumbum import local, cli, FG
from plumbum.cmd import fslroi, ImageMath
from bvec_rotation import read_bvals
import os, warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import nibabel as nib
import numpy as np

class App(cli.Application):
    """Extracts the baseline (b0) from a nifti DWI. Assumes
    the diffusion volumes are indexed by the last axis. Chooses the first b0 as the
    baseline image by default, with option to specify one."""

    dwimask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='DWI nifti mask, if mask is provided, then baseline image is masked',
        mandatory=False)

    dwi = cli.SwitchAttr(
        ['-i', '--infile'],
        cli.ExistingFile,
        help='DWI nifti image',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--outfile'],
        help= 'Extracted baseline image (default: input_prefix_bse.nii.gz)',
        mandatory=False)

    b0_threshold = cli.SwitchAttr(
        ['-t', '--threshold'],
        help= 'Threshold for b0',
        mandatory=False,
        default= 45.)

    minimum= cli.Flag(['--min'],
                      help= 'turn on this flag to choose the minimum b0 as the baseline image',
                      default= False,
                      mandatory= False)

    average= cli.Flag(['--avg'],
                      help= '''turn on this flag to choose the average of all b0 images as the baseline image, 
                            you might want to use this only when eddy/motion correction has been done before''',
                      default= False,
                      mandatory= False)


    def main(self):

        prefix= self.dwi.name.split('.')[0]
        directory= self.dwi.parent

        self.b0_threshold= float(self.b0_threshold)

        if self.out is None:
            self.out= os.path.join(directory, prefix+'_bse.nii.gz')

        if self.dwi.endswith('.nii') or self.dwi.endswith('.nii.gz'):

            bval_file= os.path.join(directory, prefix+'.bval')
            bvals= read_bvals(bval_file)
            idx= np.where([bval < self.b0_threshold for bval in bvals])[0]


            if len(idx)==1 or (not self.minimum and not self.average):
                fslroi[self.dwi, self.out, idx, 1] & FG

            elif len(idx)>1 and self.minimum:
                fslroi[self.dwi, self.out, idx, np.argsort(bvals)[0]] & FG

            elif len(idx)>1 and self.average:
                # Load the given dwi to get image data
                dwi= nib.load(self.dwi._path)
                hdr= dwi.header
                mri= dwi.get_data()

                avg_bse= np.mean(mri[:,:,:,idx], axis= 3)

                # Now write back the average bse
                mri_out = nib.nifti1.Nifti1Image(avg_bse, affine=dwi.affine, header=hdr)
                nib.save(mri_out, self.out)

            else:
                raise Exception('No b0 image found. Check the bval file.')


        else:
            raise Exception("Invalid dwi format, must be a nifti image")

        if self.dwimask:
            ImageMath(3, self.out, 'm', self.out, self.dwimask)


if __name__ == '__main__':
    App.run()
