#!/usr/bin/env python

from plumbum import cli
from plumbum.cmd import cp

import warnings
import numpy as np
from numpy import matrix, diag, linalg, vstack, hstack, array

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import nibabel as nib

from bvec_rotation import bvec_rotate
from niftiCenter import centered_origin

precision= 17


def get_spcdir_new(hdr_in):

    spcdir_orig= hdr_in.get_sform()[0:3,0:3].T

    sizes = diag(hdr_in['pixdim'][1:4])
    spcON = linalg.inv(sizes) @ spcdir_orig
    spcNN = np.zeros([3, 3])

    for i in range(0, 3):
        mi = np.argmax(abs(spcON[i, :]))
        spcNN[i, mi] = np.sign(spcON[i, mi])

    R = spcNN @ linalg.inv(spcON)

    spcdir_new = spcNN.T * sizes

    return (spcdir_new, R)


def axis_align_dwi(hdr_in, bvec_file, bval_file, out_prefix):

    spcdir_new, R= get_spcdir_new(hdr_in)

    bvec_rotate(bvec_file, out_prefix+'.bvec', rot_matrix=R)

    # rename the bval file
    cp.run([bval_file, out_prefix+'.bval'])

    return spcdir_new

def axis_align_3d(hdr_in):

    spcdir_new, _ = get_spcdir_new(hdr_in)

    return spcdir_new


def update_hdr(hdr_in, spcdir_new, offset_new):

    hdr_out= hdr_in.copy()

    xfrm= vstack((hstack((spcdir_new, array(offset_new))), [0., 0., 0., 1]))

    hdr_out.set_sform(xfrm)
    hdr_out.set_qform(xfrm)

    return hdr_out


def save_image(data, hdr_out, out_prefix):

    xfrm= hdr_out.get_sform()

    mri_out = nib.nifti1.Nifti1Image(data, affine=xfrm, header=hdr_out)

    nib.save(mri_out, out_prefix+'.nii.gz')



class Xalign(cli.Application):
    '''Axis alignment of NIFTI image'''

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

        self.img_file= str(self.img_file)

        if self.img_file.endswith('.nii') or self.img_file.endswith('.nii.gz'):
            mri= nib.load(self.img_file)
        else:
            print('Invalid image format, accepts nifti only')
            exit(1)


        hdr= mri.header
        dim= hdr['dim'][0]

        if dim == 4:
            if not self.bvec_file and not self.bval_file:
                print('bvec and bvals files not specified, exiting ...')
                exit(1)

        elif dim == 3:
            spcdir_new= axis_align_3d(hdr)

        else:
            print('Invalid image dimension, has to be either 3 or 4')


        offset_orig= matrix(hdr.get_sform()[0:3, 3]).T
        spcdir_orig= hdr.get_sform()[0:3, 0:3]


        if self.axisAlign and not self.center:
            # pass spcdir_new and offset_orig

            if not self.out_prefix:
                prefix = self.img_file.split('.')[0] + '-ax'  # a clever way to get prefix including path

            if dim == 4:
                spcdir_new= axis_align_dwi(hdr, self.bvec_file, self.bval_file, prefix)

            hdr_out = update_hdr(hdr, spcdir_new, offset_orig)


        elif not self.axisAlign and self.center:
            # pass spcdir_orig and offset_new

            if not self.out_prefix:
                prefix = self.img_file.split('.')[0] + '-ce'  # a clever way to get prefix including path

            if dim == 4:
                spcdir_new= axis_align_dwi(hdr, self.bvec_file, self.bval_file, prefix)

            offset_new = hdr['pixdim'][0] * spcdir_new @ matrix(-(hdr['dim'][1:4] - 1) / 2).T
            hdr_out = update_hdr(hdr, spcdir_orig, offset_new)


        else: # self.axisAlign and self.center:
            # pass spcdir_new and offset_new

            if not self.out_prefix:
                prefix = self.img_file.split('.')[0] + '-xc'  # a clever way to get prefix including path

            if dim == 4:
                spcdir_new= axis_align_dwi(hdr, self.bvec_file, self.bval_file, prefix)

            offset_new = hdr['pixdim'][0] * spcdir_new @ matrix(-(hdr['dim'][1:4] - 1) / 2).T
            hdr_out = update_hdr(hdr, spcdir_new, offset_new)


        # else:
        #     print('Select axisAlign and or center')
        #     exit(1)


        # write out the modified image
        save_image(mri.get_data(), hdr_out, prefix)


if __name__ == '__main__':
    Xalign.run()

'''
~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 1001-dwi.nii --bvals 1001-dwi.bval --bvecs 1001-dwi.bvec


~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 5006-dwi-shifted.nii --bvals dwi.bval --bvecs dwi.bvec.rot --center
~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 5006-dwi.nii --bvals dwi.bval --bvecs dwi.bvec.rot --axisAlign
~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 5006-dwi.nii --bvals 5006-dwi.bval --bvecs 5006-dwi.bvec --axisAlign


DWIConvert
cases=(3005 5006 7010);
for i in ${cases[@]};
do  
    cd $i;
    DWIConvert --inputVolume $i-dwi.nrrd -o $i-dwi.nii --outputBValues dwi.bval --outputBVectors dwi.bvecs \
    --conversionMode NrrdToFSL;
    cd ..;
done



cases=(3005 5006 7010);
for i in ${cases[@]};
do  
    cd $i;
    ~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i $i-dwi.nii --bvals dwi.bval --bvecs dwi.bvec.rot
    cd ..;
done


DWIConvert --inputVolume 5006-dwi.nrrd -o 5006-dwi.nii --outputBValues 5006-dwi.bval \
--outputBVectors 5006-dwi.bvecs --conversionMode NrrdToFSL

'''
