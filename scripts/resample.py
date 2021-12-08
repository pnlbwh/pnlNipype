#!/usr/bin/env python

import sys
from nibabel import load, save, Nifti1Image
from os.path import abspath, isfile
from shutil import copyfile
from multiprocessing import Pool
from glob import glob
from plumbum import local, FG
from plumbum.cmd import fslsplit, fslmerge
from plumbum.cmd import ResampleImage
import signal
from tempfile import TemporaryDirectory
import argparse
import numpy as np

N_CPU= 4

def _resample_dwi(vol):

    print('Resampling', vol)

    ResampleImage('3', vol, vol.replace('.nii.gz', '_re.nii.gz'),
                  args.size, args.size_spacing,
                  args.order, '5' if args.order == 4 else '')

def RAISE(ERR):
    raise ERR

def main():
    
    filename= abspath(args.input)
    outPrefix= abspath(args.outPrefix)
    if not isfile(filename):
        raise FileNotFoundError(f'{filename} does not exist')

    img= load(filename)

    args.size_spacing= '1' if np.array([float(x)>5 for x in args.size.strip().split('x')]).all() else '0'

    if img.header['dim'][0]==4:
        # DWI
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):

            tmpdir= local.path(tmpdir)

            print('Working directory', tmpdir)

            print('Splitting 4D')
            fslsplit(filename, 'dwi', '-t')

            volumes= glob('dwi*.nii.gz')
            volumes.sort()

            sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            pool= Pool(args.ncpu)
            signal.signal(signal.SIGINT, sigint_handler)
            try:
                pool.map_async(_resample_dwi, volumes, error_callback=RAISE)
            except KeyboardInterrupt:
                pool.terminate()
            else:
                pool.close()
            pool.join()


            volumes= glob('dwi*_re.nii.gz')
            volumes.sort()

            print('Merging 3Ds')
            fslmerge['-t', outPrefix+'.nii.gz', volumes] & FG

        inPrefix= filename.split('.nii')[0]
        copyfile(inPrefix+'.bval', outPrefix+'.bval')
        copyfile(inPrefix+'.bvec', outPrefix+'.bvec')

    else:
        # mask
        if sum(np.unique(img.get_fdata()))==1:
            ResampleImage('3', args.input, outPrefix+'.nii.gz', args.size, args.size_spacing,
                          '1', '2')

        # T1w/T2w
        else:
            ResampleImage('3', args.input, outPrefix+'.nii.gz', args.size, args.size_spacing,
                          args.order, '5' if args.order==4 else '')



if __name__=='__main__':

    parser = argparse.ArgumentParser(
        description="""Resample an MRI using ANTs ResampleImage executable. 
If the image is 4D, it is split to 3D along the last axis, resampled at 3D level, and merged back.""")

    parser.add_argument('-i','--input', help='input3D/4D MRI')
    parser.add_argument('-o', '--outPrefix',
                        help='resampled image and corresponding bval/bvec are saved with outPrefix')

    parser.add_argument('--ncpu', default= N_CPU, type= int,
                        help='default %(default)s, you can increase it at the expense of RAM')

    parser.add_argument('--size', help="""resample to MxNxO size or resolution, 
if all of M,N,O<5, it is interpreted as resolution""")

    parser.add_argument('--order', default=4,
                        help="""For details about order of interpolation, see ResampleImage --help, 
the default for masks is 1 (nearest neighbor) while for all other images it is 4 (Bspline [order=5])""")

    args = parser.parse_args()

    main()



