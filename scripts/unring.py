#!/usr/bin/env python

import sys
from dipy.denoise.gibbs import gibbs_removal
from nibabel import load, save, Nifti1Image
# from util import save_nifti
from os.path import abspath, isfile
from shutil import copyfile
from multiprocessing import Pool
from glob import glob
from plumbum import local, FG
from plumbum.cmd import fslsplit, fslmerge
import signal
from tempfile import TemporaryDirectory


def _unring(vol):
    
    print('unringing', vol)

    img= load(vol)
    unringed= gibbs_removal(img.get_fdata())
    
    outPrefix= vol.split('.nii')[0]+ '_ur'
    
    new_image= Nifti1Image(unringed, affine= img.affine, header= img.header)
    new_image.to_filename(outPrefix+'.nii.gz')



def main():
    
    filename= abspath(sys.argv[1])
    outPrefix= abspath(sys.argv[2])
    if not isfile(filename):
        raise FileNotFoundError(f'{filename} does not exist')
    
    
    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        
        tmpdir= local.path(tmpdir)

        print('Working directory', tmpdir)
        
        fslsplit(filename, 'dwi', '-t')
        
        volumes= glob('dwi*.nii.gz')
        volumes.sort()

        sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        try:
            N_CPU= int(sys.argv[3])
        except:
            N_CPU= 4

        pool= Pool(N_CPU)
        signal.signal(signal.SIGINT, sigint_handler)
        try:
            pool.map_async(_unring, volumes)
        except KeyboardInterrupt:
            pool.terminate()
        else:
            pool.close()
        pool.join()
        
        
        volumes= glob('dwi*_ur.nii.gz')
        volumes.sort()
        fslmerge['-t', outPrefix+'.nii.gz', volumes] & FG

    inPrefix= filename.split('.nii')[0] 
    copyfile(inPrefix+'.bval', outPrefix+'.bval')
    copyfile(inPrefix+'.bvec', outPrefix+'.bvec')


if __name__=='__main__':
    if len(sys.argv)==1 or sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print('Usage:\n'
              'unring.py <dwi> <outPrefix> <ncpu>\n'
              'Gibbs unringing of all DWI gradients using DIPY\n'
              'Default ncpu=4, you can increase it at the expense of RAM\n')
        exit()


    main()



