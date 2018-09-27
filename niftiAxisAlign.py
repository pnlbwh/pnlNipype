#!/usr/bin/env python

from plumbum import cli
from plumbum.cmd import cp

import warnings
import numpy as np
from numpy import matrix, diag, linalg, vstack

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import nibabel as nib

from bvec_rotation import bvec_rotate
from niftiCenter import centered_origin

precision= 17


def get_spcdir_new(hdr_in):

    spcdir_orig= hdr_in.get_sform()[0:3,0:3]

    sizes = diag([linalg.norm(spcdir_orig[0, :]), linalg.norm(spcdir_orig[1, :]), linalg.norm(spcdir_orig[2, :])])
    spcON = linalg.inv(sizes) @ spcdir_orig
    spcNN = np.zeros([3, 3])

    for i in range(0, 3):
        mi = np.argmax(abs(spcON[i, :]))
        spcNN[i, mi] = np.sign(spcON[i, mi])

    R = spcNN * linalg.inv(spcON)

    # rotation
    # spcdir_new = matrix.round(sizes @ R @ linalg.inv(sizes) @ spcdir_orig, precision)
    spcdir_new = sizes @ R @ linalg.inv(sizes) @ spcdir_orig

    return (spcdir_new, R)


def axis_align_dwi(hdr_in, bvec_file, bval_file, out_prefix):

    spcdir_new, R= get_spcdir_new(hdr_in)
    hdr_out= axis_align_3d(hdr_in, spcdir_new, R)

    bvec_rotate(bvec_file, out_prefix+'.bvec', rot_matrix=R)

    '''
    # read the bvecs
    with open(bvec_file, 'r') as f:
        bvecs = [[float(num) for num in line.split(' ')] for line in f.read().split('\n') if line]

    # making 3xN
    bvecs_T= matrix(list(map(list, zip(*bvecs))))

    # rotate the bvecs
    bvecs_T= matrix.round(R @ bvecs_T, precision)
    # bvecs_T = R @ bvecs_T

    # making Nx3 again
    bvecs = list(map(list, zip(*bvecs_T)))


    with open(out_prefix+'.bvec', 'w') as f:
        f.write(('\n').join((' ').join(str(i) for i in row) for row in bvecs))
    '''

    # rename the bval file
    cp.run([bval_file, out_prefix+'.bval'])

    return hdr_out

def axis_align_3d(hdr_in, spcdir_new= None, R= None):

    if not spcdir_new.any():
        spcdir_new, R = get_spcdir_new(hdr_in)

    hdr_out= hdr_in.copy()

    hdr_out['srow_x'][ :3]= spcdir_new[0, :]
    hdr_out['srow_y'][ :3]= spcdir_new[1, :]
    hdr_out['srow_z'][ :3]= spcdir_new[2, :]


    a = 0.50 * np.sqrt(1 + R[0,0] + R[1,1] + R[2,2])
    hdr_out['quatern_b'] = 0.25 * (R[2,1] - R[1,2]) / a
    hdr_out['quatern_c'] = 0.25 * (R[0,2] - R[2,0]) / a
    hdr_out['quatern_d'] = 0.25 * (R[1,0] - R[0,1]) / a


    hdr_out['qoffset_x']= hdr_out['srow_x'][3] # spcdir_new[0,3]
    hdr_out['qoffset_y']= hdr_out['srow_y'][3] # spcdir_new[1,3]
    hdr_out['qoffset_z']= hdr_out['srow_z'][3] # spcdir_new[2,3]

    # save_image(mri_in.get_data(), hdr_out, out_prefix)

    return hdr_out

def save_image(data, hdr_out, out_prefix):

    xfrm = vstack((hdr_out['srow_x'], hdr_out['srow_y'], hdr_out['srow_z'], [0., 0., 0., 1]))

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



        # axis alignment block ---------------------------------------------------
        if self.axisAlign:

            if not self.out_prefix:
                prefix = self.img_file.split('.')[0] + '-ax'  # a clever way to get prefix including path

            if dim == 4:
                if not self.bvec_file and not self.bval_file:
                    print('bvec and bvals files not specified, exiting ...')
                    exit(1)

                hdr_out= axis_align_dwi(hdr, self.bvec_file, self.bval_file, prefix)

            elif dim == 3:
                hdr_out= axis_align_3d(hdr)

            else:
                print('Invalid image dimension, has to be either 3 or 4')



        # centering block ---------------------------------------------------------
        if self.center:

            if not self.out_prefix and not self.axisAlign:
                prefix = self.img_file.split('.')[0] + '-ce'  # a clever way to get prefix including path

            else:
                prefix = self.img_file.split('.')[0] + '-xc'  # a clever way to get prefix including path


            hdr_out= centered_origin(hdr)



        # write out the modified image
        save_image(mri.get_data(), hdr_out, prefix)


if __name__ == '__main__':
    Xalign.run()

'''
~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 1001-dwi.nii --bvals 1001-dwi.bval --bvecs 1001-dwi.bvec


~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 5006-dwi-shifted.nii --bvals 5006-dwi.bval --bvecs 5006-dwi.bvec --center

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
    ~/Downloads/Dummy-PNL-nipype/niftiAxisAlign.py -i 1001-dwi.nii --bvals dwi.bval --bvecs dwi.bvec.rot
    cd ..;
done


DWIConvert --inputVolume 5006-dwi-shifted.nrrd -o 5006-dwi-shifted.nii --outputBValues 5006-dwi-shifted.bval \
--outputBVectors 5006-dwi-shifted.bvecs --conversionMode NrrdToFSL

'''