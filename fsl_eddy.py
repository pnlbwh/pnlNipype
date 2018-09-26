#!/usr/bin/env python

from plumbum import cli
from plumbum.cmd import eddy_openmp, bet, rm
import os

def log(msg, f):
    print(msg)
    f.write(msg+'\n')

def run_command(command, arguments, logfile):

    command_line= f'{command}.run({arguments}, retcode=None)'

    # log the command
    log(command_line, logfile)

    # execute the command
    retcode, stdout, stderr= eval(command_line)
    if retcode==0:
        log(stdout, logfile)

    else:
        log(f'{command_line} failed.', logfile)
        log(stderr, logfile)



class Eddy(cli.Application):
    '''Eddy correction using eddy_openmp command in fsl.
    For more info, see 'https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide
    or type eddy_openmp or eddy_cuda.
    '''

    dwi_file= cli.SwitchAttr(
        ['--dwi'],
        cli.ExistingFile,
        help='dwi.nii image)',
        mandatory=True)

    bvecs_file= cli.SwitchAttr(
        ['--bvecs'],
        cli.ExistingFile,
        help='bvecs file of the dwi.nii)',
        mandatory=True)

    bvals_file= cli.SwitchAttr(
        ['--bvals'],
        cli.ExistingFile,
        help='bvals file of the dwi.nii)',
        mandatory=True)

    b0_brain_mask= cli.SwitchAttr(
        ['--mask'],
        help='mask for the dwi.nii. If not provided, then a mask is created using fsl bet',
        mandatory=False)

    acqparams_file= cli.SwitchAttr(
        ['--acqp'],
        cli.ExistingFile,
        help='acuisition parameters file (.txt)',
        mandatory=True)

    index_file= cli.SwitchAttr(
        ['--index'],
        cli.ExistingFile,
        help='mapping file for (each gradient --> acquisition parameters) (.txt)',
        mandatory=True)


    betThreshold= cli.SwitchAttr(
        ['--betThreshold'],
        help='Threshold for bet mask creation',
        mandatory=False,
        default='0.3')


    def main(self):

        self.dwi_file= str(self.dwi_file)
        self.bvals_file= str(self.bvals_file)
        self.bvals_file= str(self.bvals_file)
        self.acqparams_file= str(self.acqparams_file)
        self.index_file= str(self.index_file)
        self.b0_brain_mask= str(self.b0_brain_mask)

        prefix= self.dwi_file.split('.')[0]
        directory = os.path.join(os.path.dirname(self.dwi_file), prefix+'_eddy')

        # if output directory exists, delete and re-create
        if os.path.exists(directory):
            rm.run(['-r', directory])


        logfile= open(os.path.join(directory, prefix+ '-log.txt'), 'w')

        if self.b0_brain_mask=='None':
            log('Mask not provided, creating mask ...', logfile)
            command= 'bet'
            self.b0_brain_mask = os.path.join(directory, prefix+'_mask.nii.gz')
            arguments=[self.dwi_file, prefix, '-m', '-n', '-f', self.betThreshold]
            run_command(command, arguments, logfile)

        arguments= [f'--imain={self.dwi_file}',
                    f'--mask={self.b0_brain_mask}',
                    f'--acqp={self.acqparams_file}',
                    f'--index={self.index_file}',
                    f'--bvecs={self.bvecs_file}',
                    f'--bvals={self.bvals_file}',
                    f'--out={directory+prefix}',
                    '--data_is_shelled'
                    '--verbose'] # We should be able to see output

        command= 'eddy_openmp'

        run_command(command, arguments, logfile)

        logfile.close()

if __name__== '__main__':
    Eddy.run()


'''
cd /home/tb571/Downloads/Dummy-PNL-nipype/temp_files \
/home/tb571/Downloads/Dummy-PNL-nipype/fsl_eddy.py \
--dwi 5006-dwi-xc.nii \
--bvals 5006-dwi-xc.bval \
--bvecs 5006-dwi-xc.bvec \
--acqp acqparams.txt \
--index index.txt 
'''
