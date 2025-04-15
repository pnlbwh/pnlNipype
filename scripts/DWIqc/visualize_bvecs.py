#!/usr/bin/env python

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import rand
from itertools import product, combinations
from conversion import read_bvecs, read_bvals, write_bvals
from os.path import abspath, splitext, basename
import sys

SPHERE_COLOR= 'y'
SPHERE_OPACITY= 0.3 # [0,1]
ARROW_COLOR= 'r'
ARROW_HEAD_LENGTH= 0.15 # [0,1]

B0_THRESH= 50.
B_QUANT= 50.
BSHELL_MIN_DIST= 100.


def usage():
    print('''Visualize b-vectors on a unit sphere shell-wise.
Usage:
python visualize_bvecs.py /path/to/sub-001_dwi.bvec
python visualize_bvecs.py /path/to/sub-001_dwi.bvec /path/to/sub-002_dwi.bvec
Corresponding *.bval should be in the same directory.

''')

def findBShells(bvalFile, outputBshellFile= None):

    given_bvals= read_bvals(abspath(bvalFile))

    # get unique bvalues in ascending order
    unique_bvals= np.unique(given_bvals)

    # identify b0s
    quantized_bvals= unique_bvals.copy()
    quantized_bvals[unique_bvals<=B0_THRESH]= 0.

    # round to multiple of B_QUANT (50 or 100)
    quantized_bvals= np.unique(np.round(quantized_bvals/B_QUANT)*B_QUANT)

    print('b-shell bvalues', quantized_bvals)

    bshell_indices= {}
    for bval in quantized_bvals:
        print('Indices corresponding to b-shell', bval)
        ind= np.where(abs(bval-given_bvals)<=BSHELL_MIN_DIST)[0]
        bshell_indices[bval]= ind
        print('# of volumes', len(ind))
        print(ind,'\n')


    if outputBshellFile:
        print('Saving the b-shell bvalues in', outputBshellFile)
        write_bvals(outputBshellFile, quantized_bvals)

    return quantized_bvals, bshell_indices


def plot_bvecs(bvecs, bshell, bvecs2= None):

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # draw cube
    r = [-1, 1]
    for s, e in combinations(np.array(list(product(r, r, r))), 2):
        if np.sum(np.abs(s-e)) == r[1]-r[0]:
            ax.plot3D(*zip(s, e), color='b')

    # draw sphere
    u, v = np.mgrid[0:2*np.pi:50j, 0:np.pi:50j]
    x = np.cos(u)*np.sin(v)
    y = np.sin(u)*np.sin(v)
    z = np.cos(v)
    ax.plot_surface(x, y, z, color=SPHERE_COLOR, alpha=SPHERE_OPACITY)

    L =len(bvecs)
    tails= np.zeros(L)

    q1= ax.quiver(tails,tails,tails,bvecs[:,0], bvecs[:,1], bvecs[:,2],
              normalize=True, color=ARROW_COLOR, arrow_length_ratio=ARROW_HEAD_LENGTH)


    # comparison block
    if bvecs2 is not None:
        q2= ax.quiver(tails,tails,tails,bvecs2[:,0], bvecs2[:,1], bvecs2[:,2],
                  normalize=True, color='g', arrow_length_ratio=ARROW_HEAD_LENGTH)
        ax.legend((q1,q2), ('bvecs1','bvecs2'))


    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_zlabel('Z-axis')

    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.zaxis.set_major_locator(ticker.MultipleLocator(0.5))

    ax.set_title(f'bshell {bshell}, # of b-vectors {L}')

    plt.show(block=False)


if __name__== '__main__':
    import sys
    if len(sys.argv)==1 or sys.argv[1]=='-h' or sys.argv[1]=='--help':
        usage()
        exit()

    name = splitext(abspath(sys.argv[1]))[0]
    bvecs= np.array(read_bvecs(name+'.bvec'))

    bshells, indices= findBShells(name+'.bval')

    name2= []
    if len(sys.argv) == 3:
        name2 = splitext(abspath(sys.argv[2]))[0]
        bvecs2 = np.array(read_bvecs(name2+'.bvec'))+ [0.1,0,0]


    for b in indices.keys():

        bshell_bvecs= bvecs[indices[b]]

        if not name2:
            plot_bvecs(bshell_bvecs, int(b))
        else:
            bshell_bvecs2 = bvecs2[indices[b]]
            plot_bvecs(bshell_bvecs, int(b), bvecs2= bshell_bvecs2)

    plt.show()

