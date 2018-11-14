#!/usr/bin/env python

import sys

def bvec_manual_transpose(old_bvec_file, new_bvec_file):

    with open(old_bvec_file, 'r') as f:
        # last if condition is for removing any trailing newline
        bvecs = [[num for num in line.split(' ')] for line in f.read().split('\n') if line]


    bvecs_T= list(map(list, zip(*bvecs)))

    with open(new_bvec_file, 'w') as f:
        f.write(('\n').join((' ').join(row) for row in bvecs_T))


def main():

    if sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print("Usage: bvec_transpose.py [bvecFile] [tranposedBvecFile]")
    elif len(sys.argv)==3:
        bvec_manual_transpose(sys.argv[1], sys.argv[2])
    else:
        print('Invalid arguments')
        exit(1)

if __name__== '__main__':
    main()

'''
/home/tb571/Downloads/Dummy-PNL-nipype/bvec_transpose.py dwi.bvec dwi.bvec.T
'''