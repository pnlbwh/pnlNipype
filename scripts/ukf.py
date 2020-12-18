#!/usr/bin/env python

from __future__ import print_function
from util import logfmt, TemporaryDirectory, save_nifti, load_nifti
from plumbum import local, cli, FG
from plumbum.cmd import UKFTractography

from conversion import nhdr_write

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


# default UKFTractography parameters
ukfdefaults = ['--numTensor', 2, '--stoppingFA', 0.15, '--seedingThreshold', 0.18, '--Qm', 0.001, '--Ql', 70,
               '--Rs', 0.015, '--stepLength', 0.3, '--recordLength', 1.7, '--stoppingThreshold', 0.1,
               '--seedsPerVoxel', 10, '--recordTensors']


class App(cli.Application):
    """ukf.py is a convenient script to run UKFTractography on NIFTI data.
    For NRRD data, you may run UKFTractography executable directly.
    See UKFTractography --help for more default values."""



    dwi = cli.SwitchAttr('-i', cli.ExistingFile, help='DWI in nifti', mandatory= True)
    dwimask = cli.SwitchAttr('-m', cli.ExistingFile, help='mask of the DWI in nifti', mandatory=True)
    bvalFile = cli.SwitchAttr('--bvals', cli.ExistingFile, help='bval file for DWI', mandatory= True)
    bvecFile = cli.SwitchAttr('--bvecs', cli.ExistingFile, help='bvec file for DWI', mandatory= True)
    bhigh = cli.SwitchAttr('--bhigh',
                            help='filter volumes corresponding to bval<=bhigh and run tractography on them only')
    out = cli.SwitchAttr('-o', help='output tract file (.vtk)', mandatory= True)

    givenParams = cli.SwitchAttr('--params',
                help='provide comma separated UKF parameters: --arg1,val1,--arg2,val2,--arg3,val3 (no spaces)')

    print(f'\nukf.py uses the following default values (if not provided): {ukfdefaults}\n')

    def main(self):

        with TemporaryDirectory() as tmpdir:
            tmpdir = local.path(tmpdir)
            shortdwi = tmpdir / 'dwiShort.nii.gz'
            shortmask = tmpdir / 'maskShort.nii.gz'

            tmpdwi = tmpdir / 'dwi.nhdr'
            tmpdwimask = tmpdir / 'dwimask.nhdr'

            # TODO when UKFTractography supports float32, it should be removed
            # typecast to short
            short= load_nifti(self.dwi._path)
            save_nifti(shortdwi._path, short.get_data().astype('int16'), short.affine, short.header)

            short= load_nifti(self.dwimask._path)
            save_nifti(shortmask._path, short.get_data().astype('int16'), short.affine, short.header)


            if self.bhigh:
                from conversion import grad_remove

                bhigh_prefix= tmpdir / self.dwi.stem+ f'_bhigh_{self.bhigh}'
                bhigh_dwi= bhigh_prefix+'.nii.gz'
                grad_remove(shortdwi._path, bhigh_dwi, interval=[int(self.bhigh)+50,1e6], bvalFile=self.bvalFile, bvecFile=self.bvecFile)

                shortdwi= local.path(bhigh_dwi)
                self.bvalFile = local.path(bhigh_prefix + '.bval')
                self.bvecFile = local.path(bhigh_prefix + '.bvec')

                # preserve the filtered attributes in case the user wants to run UKFTractography separately in future
                shortdwi.copy(self.dwi.dirname)
                self.bvalFile.copy(self.dwi.dirname)
                self.bvecFile.copy(self.dwi.dirname)


            # convert the dwi to NRRD
            nhdr_write(shortdwi._path, self.bvalFile._path, self.bvecFile._path, tmpdwi._path)

            # convert the mask to NRRD
            nhdr_write(shortmask._path, None, None, tmpdwimask._path)

            key_val_pair=[]

            if self.givenParams:
                key_val_pair= self.givenParams.split(',')

                for i in range(0,len(ukfdefaults)-1,2): # -1 to pass --recordTensors which is always a default

                    try:
                        ind= key_val_pair.index(ukfdefaults[i])
                        ukfdefaults[i + 1] = key_val_pair[ind + 1]
                        # since ukfdefault[i+1] has been already replaced by key_val_pair[ind+1]
                        # remove key_val_pair[ind] and [ind+1] to prevent double specification
                        key_val_pair[ind:ind+2]=[]
                    except ValueError:
                        pass


            params = ['--dwiFile', tmpdwi, '--maskFile', tmpdwimask,
                      '--seedsFile', tmpdwimask, '--tracts', self.out] + list(ukfdefaults) + key_val_pair


            logging.info('Peforming UKF tractography of {}'.format(tmpdwi))
            UKFTractography[params] & FG


if __name__ == '__main__':
    App.run()
