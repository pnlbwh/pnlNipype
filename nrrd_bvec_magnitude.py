#!/usr/bin/env python

import nrrd, sys
import numpy as np

def print_bvec_mag(filename):

    hdr= nrrd.read(filename)[1]

    b_max= float(hdr['DWMRI_b-value'])
    print('B value : {}'.format(b_max))

    ind= 0
    while True:
        try:
            bvec= [float(num) for num in hdr[f'DWMRI_gradient_{ind:04}'].split()]
            print('DWMRI_gradient_{:04} : {}'.format(ind, np.round(np.linalg.norm(bvec)**2*b_max)))
            ind+=1
        except:
            break



def main():

    if sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print("Usage: nrrd_bvec_magnitude.py [nrrd/nhdr file]")
    elif len(sys.argv)==2:
        print_bvec_mag(sys.argv[1])
    else:
        print('Invalid arguments')
        exit(1)

if __name__== '__main__':
    main()
