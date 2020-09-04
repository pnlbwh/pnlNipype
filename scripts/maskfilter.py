#!/usr/bin/env python

from scipy.ndimage import binary_erosion, binary_dilation, generate_binary_structure
from skimage.measure import label, regionprops
import numpy as np
from util import load_nifti, save_nifti
import sys
from os.path import abspath

struct_element= generate_binary_structure(3,1)

def findLargestConnectMask(img):

    mask = label(img > 0, connectivity=1)
    maxArea = 0
    for region in regionprops(mask):
        if region.area > maxArea:
            maxLabel = region.label
            maxArea = region.area

    largeConnectMask = (mask == maxLabel)

    return largeConnectMask



def single_scale(InputImage, ss):

    # erosion
    morph_image= binary_erosion(InputImage, struct_element, iterations= ss)

    # dilation
    morph_image= binary_dilation(morph_image, struct_element, iterations= ss)

    # largest connected mask
    tergest_image= findLargestConnectMask(morph_image)
    
    # OutputImage
    return morph_image



def maskfilter(maskPath, scale, filtered_maskPath):
    '''
    This python executable replicates the functionality of
    https://github.com/MRtrix3/mrtrix3/blob/master/core/filter/mask_clean.h
    It performs a few erosion and dilation to remove islands of non-brain region in a brain mask.
    '''

    mask= load_nifti(maskPath)

    filtered_mask= single_scale(mask.get_fdata(), scale)

    save_nifti(filtered_maskPath, filtered_mask, mask.affine, mask.header)



if __name__=='__main__':


    if len(sys.argv)==1 or sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print('''This python executable replicates the functionality of 
https://github.com/MRtrix3/mrtrix3/blob/master/core/filter/mask_clean.h 
It performs a few erosion and dilation to remove islands of non-brain region in a brain mask.

Usage: maskfilter input scale output

See https://github.com/MRtrix3/mrtrix3/blob/master/core/filter/mask_clean.h for details''')
        exit()

    maskPath= abspath(sys.argv[1])
    scale= int(sys.argv[2])
    filtered_maskPath= abspath(sys.argv[3])

    maskfilter(maskPath, scale, filtered_maskPath)

