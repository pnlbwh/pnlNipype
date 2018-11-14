#!/usr/bin/env python

from numpy import matrix, linalg, diag, vstack
from scipy.io import loadmat
import argparse

precision = 17

def rotate_xfrm(bvecs, xfrm_file):

    xfrm = vstack((loadmat(xfrm_file)['AffineTransform_double_3_3'].reshape(4, 3).T, [0, 0, 0, 1]))
    bvecs = vstack((bvecs, [1] * bvecs.shape[1]))

    ras2lps = diag([-1, -1, 1, 1])
    lps2ras = diag([-1, -1, 1, 1])

    # just the following command doesn't write bvecs in proper format
    # new_bvecs = ras2lps @ xfrm @ lps2ras @ bvecs

    # use the following instead
    new_bvecs= matrix.round(ras2lps @ xfrm @ lps2ras @ bvecs, precision)

    return new_bvecs[ :3,: ]

def rotate_matrix(bvecs, R):
    return matrix.round(R @ bvecs, precision)

def read_bvecs(bvec_file):

    # read the bvecs
    # try:
    #     with open(bvec_file, 'r') as f:
    #         bvecs = [[float(num) for num in line.split(' ')] for line in f.read().split('\n') if line]
    # except:
    #     with open(bvec_file, 'r') as f:
    #         bvecs = [[float(num) for num in line.split('\t')] for line in f.read().split('\n') if line]

    with open(bvec_file, 'r') as f:
        bvecs = [[float(num) for num in line.split()] for line in f.read().split('\n') if line]

    # bvec_file can be 3xN or Nx3
    # we want to return as Nx3
    if len(bvecs)==3:
        bvecs= tranpose(bvecs)

    return bvecs

def read_bvals(bval_file):

    # read the bvals
    # try:
    #     with open(bval_file, 'r') as f:
    #         bvals = [float(line) for line in f.read().split('\n') if line]
    #
    # except:
    #     with open(bval_file, 'r') as f:
    #         bvals = [float(line) for line in f.read().split(' ') if line]

    with open(bval_file, 'r') as f:
        bvals = [float(num) for num in f.read().split( )]
    
    # bval_file can be 1 line or N lines
    return bvals

def write_bvecs(bvec_file, bvecs):

    with open(bvec_file, 'w') as f:

        # when bvecs is a list
        f.write(('\n').join((' ').join(str(i) for i in row) for row in bvecs))

        # when bvecs is a matrix
        # f.write(('\n').join((' ').join(str(i) for i in row.tolist()[0]) for row in bvecs))

        # if the above block prints [], use the following instead
        # with open(out_prefix+'.bvec', 'w') as f:
        #     for row in bvecs:
        #         f.write((' ').join(str(i) for i in row)+ '\n')


def tranpose(bvecs):

    # bvecs_T = matrix(list(map(list, zip(*bvecs))))
    bvecs_T = list(map(list, zip(*bvecs)))

    return bvecs_T


def bvec_transpose(old_bvec_file, new_bvec_file):

    # read bvecs
    bvecs = read_bvecs(old_bvec_file)

    # making 3xN
    bvecs_T = tranpose(bvecs)

    # write bvecs back
    write_bvecs(new_bvec_file, bvecs_T)


def bvec_rotate(old_bvec_file, new_bvec_file, xfrm_file= None, rot_matrix= None):

    # read bvecs
    bvecs= read_bvecs(old_bvec_file)

    # making 3xN
    bvecs_T= tranpose(bvecs)

    # rotate bvecs
    if xfrm_file:
        bvecs_T = rotate_xfrm(matrix(bvecs_T), xfrm_file)
    else:
        bvecs_T = rotate_matrix(matrix(bvecs_T), rot_matrix)


    # making Nx3 again
    bvecs = tranpose(bvecs_T)

    # write bvecs back
    write_bvecs(new_bvec_file, bvecs)



def main():

    parser = argparse.ArgumentParser(description='Rotate bvecs given a transformation')
    parser.add_argument('-i', '--input', type= str, required= True, help='input bvec file')
    parser.add_argument('-o', '--output', type= str, required= True, help='output bvec file')
    parser.add_argument('-x', '--xfrm', type= str, help= '''.mat file containing a 3x4 transformation matrix
                        (4th row [0,0,0,1] is automatically appended)''')

    parser.add_argument('-t', '--transpose', help='turn on this flag for just transposing the input bvecs',
                        action= 'store_true')

    args = parser.parse_args()


    old_bvec_file= args.input
    new_bvec_file= args.output

    if args.transpose:
        bvec_transpose(old_bvec_file, new_bvec_file)

    else:
        if not args.xfrm:
            print('Transform file missing')
            exit(1)

        bvec_rotate(old_bvec_file, new_bvec_file, xfrm_file= args.xfrm)



if __name__== '__main__':
    main()

'''
/home/tb571/Downloads/Dummy-PNL-nipype/bvec_rotation.py -i dwi.bvec -x 5006.mat -o dwi.bvec.rot \
/home/tb571/Downloads/Dummy-PNL-nipype/bvec_rotation.py -i dwi.bvec -o dwi.bvec.T -t
'''

'''
cases=(3005 5006 7010);
for i in ${cases[@]};
do  
    cd $i;
     /home/tb571/Downloads/Dummy-PNL-nipype/bvec_rotation.py \
     -i dwi.bvec -o dwi.bvec.rot -x $i.mat;
    cd ..;
done
'''