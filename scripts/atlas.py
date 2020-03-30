#!/usr/bin/env python
from __future__ import print_function
from plumbum import local, cli, FG
from plumbum.cmd import ComposeMultiTransform, antsApplyTransforms, MeasureImageSimilarity, \
    head, cut, antsRegistration
from itertools import zip_longest
import pandas as pd
from glob import glob
import numpy as np
import sys, os
import multiprocessing
from math import exp
from conversion.antsUtil import antsReg
from util import logfmt, save_nifti, TemporaryDirectory, load_nifti, N_CPU, N_PROC, dirname, pjoin

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))


# determine ANTS_VERSION
# $ antsRegistration --version
#   ANTs Version: 2.2.0.dev233-g19285
#   Compiled: Sep  2 2018 23:23:33

antsVerFile='/tmp/ANTS_VERSION_'+os.environ['USER']
(antsRegistration['--version'] > antsVerFile) & FG
with open(antsVerFile) as f:
      content=f.read().split('\n')
      ANTS_VERSION= content[0].split()[-1]

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format=logfmt(__file__))

ANTSJOINTFUSION_PARAMS = ['--search-radius', 5
                         ,'--patch-radius',3
                         ,'--patch-metric','PC'
                         ,'--constrain-nonnegative',1
                         ,'--alpha', 0.4
                         ,'--beta', 3.0]

# with the omission of subcommands, this function is not used anymore
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    if n == 1:
        return [iterable]
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def computeWarp(image, target, out):

    with TemporaryDirectory() as tmpdir:
        tmpdir = local.path(tmpdir)
        pre = tmpdir / 'ants'
        warp = pre + '1Warp.nii.gz'
        affine = pre + '0GenericAffine.mat'

        # pre is the prefix (directory) for saving 1Warp.nii.gz and 0GenericAffine.mat
        antsReg(target, None, image, pre)

        # out is Warp{idx}.nii.gz, saved in the specified output direcotry
        # ComposeMultiTransform combines the 1Warp.nii.gz and 0GenericAffine.mat into a Warp{idx}.nii.gz file
        ComposeMultiTransform('3', out, '-R', target, warp, affine)



def applyWarp(moving, warp, reference, out, interpolation='Linear'):
    '''Interpolation options:
    Linear
    NearestNeighbor
    MultiLabel[<sigma=imageSpacing>,<alpha=4.0>]
    Gaussian[<sigma=imageSpacing>,<alpha=1.0>]
    BSpline[<order=3>]
    CosineWindowedSinc
    WelchWindowedSinc
    HammingWindowedSinc
    LanczosWindowedSinc
    GenericLabel[<interpolator=Linear>]
    '''

    # antsApplyTransforms reads Warp{idx}.nii.gz and 
    # creates atlas{idx}.nii.gz and {labelname}{idx}.nii.gz in the specified ouput directory
    antsApplyTransforms['-d', '3', '-i', moving, '-t', warp, '-r', reference,
                        '-o', out, '--interpolation', interpolation] & FG


def computeMI(target, img, miFile):

    if ANTS_VERSION <= '2.1.0':
        (MeasureImageSimilarity['3', '2', target, img] | head['-n', '-2'] | cut['-d ', '-f6'] > miFile)()

    else:
        (MeasureImageSimilarity['-d', '3', '-m', 'MI[{},{},1,256]'.format(target, img)] > miFile) & FG


def weightsFromMIExp(mis, alpha):
    factor = alpha / (max(mis) - min(mis))
    weights = [exp(factor * (min(mis) - mi)) for mi in mis]
    return [w / sum(weights) for w in weights]

def fuseWeightedAvg(labels, weights, out, target_header):

    # for each label, fuse warped labelmaps to compute output labelmap
    print("Apply weights to warped training {} et al., fuse, and threshold".format(labels[0]))
    data= np.zeros(target_header['dim'][1:4], dtype= 'float32')
    for label, w in zip(labels, weights):
        data+= load_nifti(label._path).get_data()*w


    # out is {labelname}.nii.gz
    save_nifti(out, ((data>0.5)*1).astype('uint8'), target_header.get_best_affine(), target_header)

    print("Made labelmap: " + out)


def fuseAntsJointFusion(target, images, labels, out):
    from plumbum.cmd import antsJointFusion

    # images are the warped images atlas{idx}.nii.gz
    # labelmaps are the warped labels {labelname}{idx}.nii.gz
    # out is {labelname}.nii.gz
    antsJointFusionArgs = \
        ['-d', 3 ,'-t', target ,'-g'] + \
        images + \
        ['-l'] +  \
        labels + \
        ['-o', out] + \
        ['--verbose']

    antsJointFusion[antsJointFusionArgs] & FG

    print("Made labelmap: " + out)


def fuseAvg(labels, out, target_header):
    from plumbum.cmd import AverageImages

    with TemporaryDirectory() as tmpdir:
        nii = local.path(tmpdir) / 'avg.nii.gz'
        AverageImages['3', nii, '0', labels] & FG

        img= load_nifti(nii._path)
        # Binary operation, if out>0.5, pipe the output and save as {labelname}.nii.gz
        # out is {labelname}.nii.gz
        save_nifti(out, ((img.get_data()>0.5)*1).astype('uint8'), target_header.get_best_affine(), target_header)


    print("Made labelmap: " + out)


def train2target(itr):

    idx, attr = itr
    outdir, target= attr[-2: ]
    r= attr[:-2]

    print('Registering image {} to target'.format(idx))
    warp = outdir / 'warp{}.nii.gz'.format(idx)
    atlas = outdir / 'atlas{}.nii.gz'.format(idx)
    logging.info('Making {}'.format(atlas))

    # warp is computed among the first column images and the target image
    # then that warp is applied to images in other columns
    # assuming first column of the dictionary contains moving images
    computeWarp(r[0], target, warp)  # first column of each row is used here
    applyWarp(r[0], warp, target, atlas)  # first column of each row is used here

    # labelname is the column header and label is the image in the csv file
    for labelname, label in r.iloc[1:].iteritems():  # rest of the columns of each row are used here
        atlaslabel = outdir / '{}{}.nii.gz'.format(labelname,idx)
        logging.info('Making {}'.format(atlaslabel))

        # creates {labelname}{idx}.nii.gz in the output directory
        # applying Warp{idx}.nii.gz on each image under 'labelname' column in the csv file


        applyWarp(label,
                  warp,
                  target,
                  atlaslabel,
                  interpolation='NearestNeighbor')


def makeAtlases(target, trainingTable, outPrefix, fusion, threads, debug):

    with TemporaryDirectory() as tmpdir:

        tmpdir = local.path(tmpdir)

        L= len(trainingTable)

        multiDataFrame= pd.concat([trainingTable, pd.DataFrame({'tmpdir': [tmpdir]*L, 'target': [str(target)]*L})], axis= 1)

        logging.info('Create {} atlases: compute transforms from images to target and apply over images'.format(L))

        pool = multiprocessing.Pool(threads)  # Use all available cores, otherwise specify the number you want as an argument

        pool.map_async(train2target, multiDataFrame.iterrows())

        pool.close()
        pool.join()

        logging.info('Fuse warped labelmaps to compute output labelmaps')
        atlasimages = tmpdir // 'atlas*.nii.gz'
        # sorting is required for applying weight to corresponding labelmap
        atlasimages.sort()

        if fusion.lower() == 'wavg':

            ALPHA_DEFAULT= 0.45

            logging.info('Compute MI between warped images and target')
            pool = multiprocessing.Pool(threads)
            for img in atlasimages:
                print('MI between {} and target'.format(img))
                miFile= img+'.txt'
                pool.apply_async(func= computeMI, args= (target, img, miFile, ))

            pool.close()
            pool.join()

            mis= []
            with open(tmpdir+'/MI.txt','w') as fw:

                for img in atlasimages:
                    with open(img+'.txt') as f:
                        mi= f.read().strip()
                        fw.write(img+','+mi+'\n')
                        mis.append(float(mi))

            weights = weightsFromMIExp(mis, ALPHA_DEFAULT)

        target_header= load_nifti(target._path).header
        pool = multiprocessing.Pool(threads)  # Use all available cores, otherwise specify the number you want as an argument
        for labelname in list(trainingTable)[1:]:  # list(d) gets column names

            out = os.path.abspath(outPrefix+ f'_{labelname}.nii.gz')
            if os.path.exists(out):
                os.remove(out)
            labelmaps = tmpdir // (labelname + '*')
            labelmaps.sort()

            if fusion.lower() == 'avg':
                print(' ')
                # parellelize
                # fuseAvg(labelmaps, out, target_header)
                pool.apply_async(func= fuseAvg, args= (labelmaps, out, target_header, ))

            elif fusion.lower() == 'antsjointfusion':
                print(' ')
                # atlasimages are the warped images
                # labelmaps are the warped labels
                # parellelize
                # fuseAntsJointFusion(target, atlasimages, labelmaps, out)
                pool.apply_async(func= fuseAntsJointFusion, args= (target, atlasimages, labelmaps, out, ))

            elif fusion.lower() == 'wavg':
                print(' ')
                # parellelize
                # fuseWeightedAvg(labelmaps, weights, out, target_header)
                pool.apply_async(func= fuseWeightedAvg, args= (labelmaps, weights, out, target_header, ))

            else:
                print('Unrecognized fusion option: {}. Skipping.'.format(fusion))

        pool.close()
        pool.join()

        if debug:
            tmpdir.copy(pjoin(dirname(outPrefix), 'atlas-debug-' + str(os.getpid())))


class Atlas(cli.Application):
    """Makes atlas image/labelmap pairs for a target image. Option to merge labelmaps via averaging
    or AntsJointFusion."""

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code



# @Atlas.subcommand("csv")
class AtlasCsv(cli.Application):
    """Makes atlas image/labelmap pairs for a target image.
    Option to merge labelmaps via averaging or AntsJointFusion.
    Specify training images and labelmaps via a csv file.
    Put the images with any header in the first column, 
    and labelmaps with proper headers in the consecutive columns. 
    The headers in the labelmap columns will be used to name the generated atlas labelmaps.
    """

    target = cli.SwitchAttr(
        ['-t', '--target'],
        cli.ExistingFile,
        help='target image',
        mandatory=True)
    fusions = cli.SwitchAttr(
        ['--fusion'],
        cli.Set("avg", "wavg", "antsJointFusion", case_sensitive=False),
        help='Also create predicted labelmap(s) by combining the atlas labelmaps: '
             'avg is naive mathematical average, wavg is weighted average where weights are computed from MI '
             'between the warped atlases and target image, antsJointFusion is local weighted averaging', default='wavg')
    out = cli.SwitchAttr(
        ['-o', '--outPrefix'],
        help='output prefix, output labelmaps are saved as outPrefix_mask.nii.gz, outPrefix_cingr.nii.gz, ...',
        mandatory=True)
    threads= cli.SwitchAttr(['-n', '--nproc'],
        help='number of processes/threads to use (-1 for all available)',
        default= N_PROC)
    debug = cli.Flag('-d', help='Debug mode, saves intermediate labelmaps to atlas-debug-<pid> in output directory')
    csvFile = cli.SwitchAttr(['--train'],
        help='--train t1; --train t2; --train trainingImages.csv; '
        'see pnlNipype/docs/TUTORIAL.md to know what each value means')

    # @cli.positional(cli.ExistingFile)
    def main(self):
        
        if self.csvFile=='t1' or self.csvFile=='t2':
            PNLPIPE_SOFT = os.getenv('PNLPIPE_SOFT')
            if not PNLPIPE_SOFT:
                raise EnvironmentError('Define the environment variable PNLPIPE_SOFT from where training data could be obtained')

        if self.csvFile=='t1':
            self.csvFile=glob(PNLPIPE_SOFT+'/trainingDataT1AHCC-*/trainingDataT1Masks-hdr.csv')[0]
        elif self.csvFile=='t2':
            self.csvFile=glob(PNLPIPE_SOFT+'/trainingDataT2Masks-*/trainingDataT2Masks-hdr.csv')[0]
        
        trainingTable = pd.read_csv(self.csvFile)
        makeAtlases(self.target, trainingTable, self.out, self.fusions, int(self.threads), self.debug)
        logging.info('Made ' + self.out + '_*.nii.gz')


if __name__ == '__main__':
    # Atlas.run()
    AtlasCsv.run()
