#!/usr/bin/env python

import numpy as np
from bvec_rotation import read_bvecs, read_bvals
import argparse

def main():

    parser = argparse.ArgumentParser(description='Given path prefix, prints bvals and bvecs')
    parser.add_argument('-p', '--prefix', type=str, required=True, 
                        help='prefix for prefix.bval and prefix.bvec files')

    args = parser.parse_args()

    prefix= args.prefix
    bval_file= prefix+'.bval'
    bvec_file= prefix+'.bvec'

    bvecs= read_bvecs(bvec_file)

    bvals= read_bvals(bval_file)

    print('bval\tscaled_bvec_magnitude')
    for (val, vec) in zip(bvals, np.round(np.linalg.norm(bvecs, axis= 1)**2*max(bvals))):
        print(f'{val}\t{vec}')

if __name__ == '__main__':
    main()