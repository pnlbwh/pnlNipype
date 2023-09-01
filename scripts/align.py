#!/usr/bin/env python

from plumbum import cli
import numpy as np
from numpy import matrix, diag, linalg, vstack, hstack, array

from util import load_nifti, save_nifti

from conversion.bval_bvec_io import bvec_rotate

import warnings

precision= 17


def get_spcdir_new(hdr_in):

    spcdir_orig= hdr_in.get_best_affine()[0:3,0:3].T

    sizes = diag(hdr_in['pixdim'][1:4])
    spcON = linalg.inv(sizes) @ spcdir_orig
    spcNN = np.zeros([3, 3])

    for i in range(0, 3):
        mi = np.argmax(abs(spcON[i, :]))
        spcNN[i, mi] = np.sign(spcON[i, mi])

    R = spcNN @ linalg.inv(spcON)

    spcdir_new = spcNN.T @ sizes

    return (spcdir_new, R)


def axis_align_dwi(hdr_in, bvec_file, bval_file, out_prefix):

    spcdir_new, R= get_spcdir_new(hdr_in)

    # bvecs are in IJK space, so no change due to axis alignment

    return spcdir_new

def axis_align_3d(hdr_in):

    spcdir_new, _ = get_spcdir_new(hdr_in)

    return spcdir_new


def update_hdr(hdr_in, spcdir_new, offset_new):

    hdr_out= hdr_in.copy()

    xfrm= vstack((hstack((spcdir_new, array(offset_new))), [0., 0., 0., 1]))

    hdr_out.set_sform(xfrm, code= 'aligned')
    hdr_out.set_qform(xfrm, code= 'aligned')
    
    return hdr_out


class Xalign(cli.Application):
    '''Axis alignment and centering of a 3D/4D NIFTI image'''

    img_file = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='a 3d or 4d nifti image',
        mandatory=True)

    bvec_file= cli.SwitchAttr(
        ['--bvecs'],
        cli.ExistingFile,
        help='bvec file',
        mandatory=False)


    bval_file= cli.SwitchAttr(
        ['--bvals'],
        cli.ExistingFile,
        help='bval file',
        mandatory=False)

    out_prefix = cli.SwitchAttr(
        ['-o', '--outPrefix'],
        help='prefix for naming dwi, bval, and bvec files',
        mandatory=False)

    axisAlign = cli.Flag(
        ['--axisAlign'],
        help='turn on for axis alignment',
        mandatory=False,
        default= False)

    center = cli.Flag(
        ['--center'],
        help='turn on for centering',
        mandatory=False,
        default= False)


    def main(self):


        if self.img_file.endswith('.nii') or self.img_file.endswith('.nii.gz'):
            mri= load_nifti(self.img_file._path)
        else:
            print('Invalid image format, accepts nifti only')
            exit(1)


        hdr= mri.header
        dim= hdr['dim'][0]

        if dim == 4:
            if not self.bvec_file and not self.bval_file:
                # fMRI will not have bvec/bval, so only raise a warning
                warnings.warn('Seems like a DWI but bvec/bval files not specified')

        elif dim == 3:
            spcdir_new= axis_align_3d(hdr)

        else:
            print('Invalid image dimension, has to be either 3 or 4')


        offset_orig= matrix(hdr.get_best_affine()[0:3, 3]).T
        spcdir_orig= hdr.get_best_affine()[0:3, 0:3]


        if self.axisAlign and not self.center:
            # pass spcdir_new and offset_orig

            if not self.out_prefix:
                self.out_prefix = self.img_file.split('.')[0] + '-ax'  # a clever way to get prefix including path

            if dim == 4:
                spcdir_new= axis_align_dwi(hdr, self.bvec_file, self.bval_file, self.out_prefix)

            hdr_out = update_hdr(hdr, spcdir_new, offset_orig)


        elif not self.axisAlign and self.center:
            # pass spcdir_orig and offset_new

            if not self.out_prefix:
                self.out_prefix = self.img_file.split('.')[0] + '-ce'  # a clever way to get prefix including path


            offset_new = -spcdir_orig @ matrix((hdr['dim'][1:4] - 1) / 2).T
            hdr_out = update_hdr(hdr, spcdir_orig, offset_new)


        else: # self.axisAlign and self.center:
            # pass spcdir_new and offset_new

            if not self.out_prefix:
                self.out_prefix = self.img_file.split('.')[0] + '-xc'  # a clever way to get prefix including path

            if dim == 4:
                spcdir_new= axis_align_dwi(hdr, self.bvec_file, self.bval_file, self.out_prefix)

            offset_new = -spcdir_new @ matrix((hdr['dim'][1:4] - 1) / 2).T
            hdr_out = update_hdr(hdr, spcdir_new, offset_new)


        # Goldstein's data has one b0 but accompanying bval and bvec
        # That means any 3D image can come with bval and bvec
        # Since axis alignment and centering do not affect bval and bvec
        # copy them whenever provided
        try:
            # rename the bval file
            self.bval_file.copy(self.out_prefix + '.bval')
            # rename the bvec file
            self.bvec_file.copy(self.out_prefix + '.bvec')
        except:
            pass


        # write out the modified image
        save_nifti(self.out_prefix+'.nii.gz', mri.get_data(), hdr_out.get_best_affine(), hdr_out)


if __name__ == '__main__':
    Xalign.run()

