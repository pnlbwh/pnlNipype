#!/usr/bin/env python

from __future__ import print_function
from os import getpid
from util import logfmt, TemporaryDirectory, pjoin, FILEDIR, N_PROC, dirname
from plumbum import local, cli, FG
from plumbum.cmd import ls, flirt, fslmerge, tar, fslsplit
import numpy as np
import sys
from multiprocessing import Pool
from subprocess import check_call
from conversion import read_bvecs, write_bvecs

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

def _Register_vol(volnii):

    logging.info('Run FSL flirt affine registration')
    flirt('-interp' ,'sinc'
          ,'-sincwidth' ,'7'
          ,'-sincwindow' ,'blackman'
          ,'-in', volnii
          ,'-ref', 'b0.nii.gz'
          ,'-nosearch'
          ,'-o', volnii
          ,'-omat', volnii.with_suffix('.txt', depth=2)
          ,'-paddingsize', '1')

    return volnii

class App(cli.Application):
    '''Eddy current correction.'''

    debug = cli.Flag('-d', help='Debug, saves registrations to eddy-debug-<pid>')
    dwi = cli.SwitchAttr('-i', cli.ExistingFile, help='DWI in nifti', mandatory= True)
    bvalFile = cli.SwitchAttr('--bvals', cli.ExistingFile, help='bval file for DWI', mandatory= True)
    bvecFile = cli.SwitchAttr('--bvecs', cli.ExistingFile, help='bvec file for DWI', mandatory= True)
    out = cli.SwitchAttr('-o', help='Prefix for eddy corrected DWI', mandatory= True)
    overwrite = cli.Flag('--force', default=False, help='Force overwrite')
    nproc = cli.SwitchAttr(
        ['-n', '--nproc'], help='''number of threads to use, if other processes in your computer 
        becomes sluggish/you run into memory error, reduce --nproc''', default= N_PROC)

    def main(self):
        self.out = local.path(self.out)
        if self.out.exists():
            if self.overwrite:
                self.out.delete()
            else:
                logging.error("{} exists, use '--force' to overwrite it".format(self.out))
                sys.exit(1)

        outxfms = self.out.dirname / self.out.stem+'_xfms.tgz'

        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
            tmpdir = local.path(tmpdir)

            dicePrefix = 'vol'

            logging.info('Dice the DWI')
            fslsplit[self.dwi] & FG

            logging.info('Extract the B0')
            check_call((' ').join([pjoin(FILEDIR,'bse.py'), '-i', self.dwi._path, 
                                   '--bvals', self.bvalFile, '-o', 'b0.nii.gz']), shell= True)

            logging.info('Register each volume to the B0')
            vols = sorted(tmpdir // (dicePrefix + '*.nii.gz'))

            # use the following multi-processed loop
            pool= Pool(int(self.nproc))
            res= pool.map_async(_Register_vol, vols)
            volsRegistered= res.get()
            pool.close()
            pool.join()

            # or use the following for loop
            # volsRegistered = []
            # for vol in vols:
            #     volnii = vol.with_suffix('.nii.gz')
            #     logging.info('Run FSL flirt affine registration')
            #     flirt('-interp' ,'sinc'
            #           ,'-sincwidth' ,'7'
            #           ,'-sincwindow' ,'blackman'
            #           ,'-in', volnii
            #           ,'-ref', 'b0.nii.gz'
            #           ,'-nosearch'
            #           ,'-o', volnii
            #           ,'-omat', volnii.with_suffix('.txt', depth=2)
            #           ,'-paddingsize', '1')
            #     volsRegistered.append(volnii)


            fslmerge('-t', 'EddyCorrect-DWI.nii.gz', volsRegistered)
            transforms = tmpdir.glob(dicePrefix+'*.txt')
            transforms.sort()


            logging.info('Extract the rotations and realign the gradients')

            bvecs= read_bvecs(self.bvecFile._path)
            bvecs_new= bvecs.copy()
            for (i,t) in enumerate(transforms):

                logging.info('Apply ' + t)
                tra = np.loadtxt(t)

                # removes the translation
                aff = np.matrix(tra[0:3,0:3])

                # computes the finite strain of aff to get the rotation
                rot = aff*aff.T

                # compute the square root of rot
                [el, ev] = np.linalg.eig(rot)
                eL = np.identity(3)*np.sqrt(el)
                sq = ev*eL*ev.I

                # finally the rotation is defined as
                rot = sq.I*aff

                bvecs_new[i] = np.dot(rot,bvecs[i]).tolist()[0]



            tar('cvzf', outxfms, transforms)

            # save modified bvecs
            write_bvecs(self.out._path+'.bvec', bvecs_new)

            # save EddyCorrect-DWI
            local.path('EddyCorrect-DWI.nii.gz').copy(self.out._path+'.nii.gz')

            # copy bvals
            self.bvalFile.copy(self.out._path+'.bval')

            if self.debug:
                tmpdir.copy(pjoin(dirname(self.out),"eddy-debug-"+str(getpid())))


if __name__ == '__main__':
    App.run()
