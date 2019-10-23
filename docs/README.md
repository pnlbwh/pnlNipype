![](../Misc/pnl-bwh-hms.png)

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.3258854.svg)](https://doi.org/10.5281/zenodo.3258854) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64-orange.svg)]()

Developed by Tashrif Billah, Sylvain Bouix, and Yogesh Rathi, Brigham and Women's Hospital (Harvard Medical School).


Table of Contents
=================

   * [Table of Contents](#table-of-contents)
   * [Citation](#citation)
   * [Introduction](#introduction)
   * [Dependencies](#dependencies)
   * [Installation](#installation)
      * [1. Install prerequisites](#1-install-prerequisites)
         * [i. With pnlpipe](#i-with-pnlpipe)
         * [ii. Independently](#ii-independently)
            * [Check system architecture](#check-system-architecture)
            * [Python 3](#python-3)
            * [FSL](#fsl)
            * [FreeSurfer](#freesurfer)
            * [pnlpipe software](#pnlpipe-software)
      * [2. Configure your environment](#2-configure-your-environment)
      * [3. Temporary directory](#3-temporary-directory)
      * [4. Tests](#4-tests)
         * [i. Preliminary](#i-preliminary)
         * [ii. Detailed](#ii-detailed)
   * [Multiprocessing](#multiprocessing)
   * [Pipeline scripts overview](#pipeline-scripts-overview)
   * [Global bashrc](#global-bashrc)
   * [Documentation](#documentation)
   * [Support](#support)
   
   
Table of Contents created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)


# Citation

If this pipeline is useful in your research, please cite as below:

Billah, Tashrif; Bouix, Sylvain; Rathi, Yogesh; NIFTI MRI processing pipeline,
https://github.com/pnlbwh/pnlNipype, 2019, DOI: 10.5281/zenodo.3258854


# Introduction

*pnlNipype* is a Python-based framework for processing anatomical (T1, T2) and diffusion weighted images.
It comprises some of the [PNL](http://pnl.bwh.harvard.edu)'s neuroimaging pipelines. 
A pipeline is a directed acyclic graph (DAG) of dependencies.
The following diagram depicts functionality of the NIFTI pipeline, where
each node represents an output, and the arrows represent dependencies:

![](Misc/dag.png)



# Dependencies

* dcm2niix
* ANTs == 2.3.0
* UKFTractography == 1.0
* freesurfer >= 5.0.3 
* FSL >= 5.0.3
* python >= 3


# Installation

## 1. Install prerequisites

### i. With pnlpipe

*pnlNipype* depends on the above software modules. It is recommended to follow *pnlpipe* installation [instruction](https://github.com/pnlbwh/pnlpipe#installation).
Most of the requisite software modules will be installed with *pnlpipe*. In addition, you should also learn 
how to [configure your environment](https://github.com/pnlbwh/pnlpipe#1-configure-your-environment) and [source individual software module](https://github.com/pnlbwh/pnlpipe#2-source-individual-software-module).

### ii. Independently

Installing *pnlNipype* independently should require you to install each of the dependencies separately. 
This way, you can have more control upon the requisite software modules. The independent installation is for users with 
a little more programming knowledge.

Install the following software (ignore the one(s) you have already):

* Python 3
* FreeSurfer>=5.0.3
* FSL>=5.0.11

    
#### Check system architecture

    uname -a # check if 32 or 64 bit

#### Python 3

Download [Miniconda Python 3.6 bash installer](https://conda.io/miniconda.html) (32/64-bit based on your environment):
    
    sh Miniconda3-latest-Linux-x86_64.sh -b # -b flag is for license agreement

Activate the conda environment:

    source ~/miniconda3/bin/activate # should introduce '(base)' in front of each line

#### FSL

Follow the [instruction](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation) to download and install FSL.

#### FreeSurfer
    
Follow the [instruction](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) to download and install FreeSurfer >= 5.0.3
After installation, you can check FreeSurfer version by typing `freesurfer` on the terminal.

#### pnlpipe software

The rest of the software can be installed with *pnlpipe* infrastructure:
    
    git clone --recurse-submodules https://github.com/pnlbwh/pnlNipype.git && cd pnlNipype
    
    # define PYTHONPATH so following software installation scripts are found
    export PYTHONPATH=/abs/directory/of/pnlpipe_software/
    
    # this is where software modules are installed
    export PNLPIPE_SOFT=/directory/for/software/
    
    # https://github.com/pnlbwh/ukftractography
    cmd/install.py UKFTractography
    
    # https://github.com/rordenlab/dcm2niix
    cmd/install.py dcm2niix
    
    # https://github.com/ANTsX/ANTs
    cmd/install.py ANTs
    
    # https://github.com/demianw/tract_querier
    cmd/install.py tract_querier
    
    # https://github.com/pnlbwh
    cmd/install.py trainingDataT1AHCC
    cmd/install.py trainingDataT2Masks
    
    # finally, install the python packages required to run pnlNipype
    pip install -r requirements.txt
    

Detailed instruction can be found [here](https://github.com/pnlbwh/pnlpipe_software).


You may also build the following from source:

* ANTs

You can build ANTs from [source](https://github.com/ANTsX/ANTs). Additionally, you should define [ANTSPATH](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS#set-path-and-antspath)
    
* dcm2niix

dcm2niix executable will create NIFTI file from DICOM. The pipeline uses a reliable converter dcm2niix. 
Building of dcm2niix is very straightforward and reliable. Follow [this](https://github.com/rordenlab/dcm2niix#build-command-line-version-with-cmake-linux-macos-windows) instruction to build dcm2niix.

* UKFTractography

Follow this [instruction](https://github.com/pnlbwh/ukftractography/blob/master/README.md) to download and install UKFTractography.



## 2. Configure your environment

If you have already configured your environment following *pnlpipe*, you may pass the instruction below:

    source ~/miniconda3/bin/activate           # should introduce '(base)' in front of each line
    export FSLDIR=~/fsl/                       # setup fsl environment
    source $FSLDIR/etc/fslconf/fsl.sh
    export PATH=$PATH:$FSLDIR/bin
    export FREESURFER_HOME=~/freesurfer        # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export ANTSPATH=/path/to/ANTs/bin/
    export PATH=$ANTSPATH:ANTs/Scripts:$PATH   # define ANTSPATH and export ANTs scripts in your path
    export PATH=~/dcm2niix/build/bin
    
    
*(If you would like, you may edit your [bashrc](#global-bashrc) to have environment automatically setup
every time you open a new terminal)*

## 3. Temporary directory

Both *pnlpipe* and *pnlNipype* have centralized control over various temporary directories created down the pipeline. 
The temporary directories can be large, and may possibly clog the default `/tmp/` directory. You may define custom 
temporary directory with environment variable `PNLPIPE_TMPDIR`:

    mkdir ~/tmp/
    export PNLPIPE_TMPDIR=~/tmp/

## 4. Tests

### i. Preliminary

Upon successful installation, you should be able to see help message of each script in the pipeline:
    
    cd lib
    scripts/atlas.py --help
    scripts/fs2dwi.py --help
    ...


### ii. Detailed

This section will be elaborated in future.
    


# Multiprocessing

Multi-processing is an advanced feature of *pnlNipype*. The following scripts are able to utilize 
python multiprocessing capability:

    atlas.py
    pnl_eddy.py
    pnl_epi.py
    wmql.py
    antsApplyTransformsDWI.py
     
     
You may specify `N_PROC` parameter in [scripts/util.py](scripts/util.py) for default number of processes to be used across scripts in the pipeline.

    N_PROC = '4'
    
On a Linux machine, you should find the number of processors by the command `lscpu`:

    On-line CPU(s) list:   0-55 

You can specify any number not greater than the On-line CPU(s). However, one caveat is, other applications in your computer 
may become sluggish or you may run into memory error due to heavier computation in the background. If this is the case, 
reduce NCPU (`--nproc`) to less than 4.



# Pipeline scripts overview

`scripts` is a directory of PNL specific scripts that implement various
pipeline steps. These scripts are the successors to the ones in [pnlpipe](https://github.com/pnlbwh/pnpipe)
used for NRRD format data. Besides being more robust and up to date with respect to software such
as [ANTS](http://stnava.github.io/ANTs/), they are implemented in python using
the shell scripting library [plumbum](https://plumbum.readthedocs.io/en/latest/).
Being written in python means they are easier to understand and modify,
and [plumbum](https://plumbum.readthedocs.io/en/latest/) allows them to be
almost as concise as a regular shell script.

You can call any of these scripts directly, e.g.

    scripts/align.py -h


It's important to note that usually the scripts are calling other binaries, such
as those in *ANTS*, *FreeSurfer* and *FSL*. So, make sure you source each of their environments 
so individual scripts are able to find them.

This table summarizes the scripts in `pnlNipype/scripts/`:

| Category           |  Script                            |  Function                                                             |
|--------------------|------------------------------------|-----------------------------------------------------------------------|
| General            |  **align.py**                      |  axis aligns and centers an image                                     |
| General            |  **bet_mask.py**                   |  masks a 3D/4D MRI using FSL bet                                      |
| General            |  **masking.py**                    |  skullstrips by applying a labelmap mask                              |
| -                  |  -                                 |  -                                                                    |
| DWI                |  **antsApplyTransformsDWI.py**     |  applies a transform to a DWI                                         |
| DWI                |  **bse.py**                        |  extracts a baseline b0 image                                         |
| -                  |  -                                 |  -                                                                    |
| DWI                |  **pnl_epi.py**                    |  corrects EPI distortion via registration                             |
| DWI                |  **fsl_topup_epi_eddy.py**         |  corrects EPI distortion using FSL topup and eddy_openmp              |
| -                  |  -                                 |  -                                                                    |
| DWI                |  **pnl_eddy.py**                   |  corrects eddy distortion via registration                            |
| DWI                |  **fsl_eddy.py**                   |  corrects eddy distortion using FSL eddy_openmp                       |
| DWI                |  **ukf.py**                        |  convenient script for running UKFTractography                        |
| -                  |  -                                 |  -                                                                    |
| Structural         |  **atlas.py**                      |  computes a brain mask from training data                             |
| Structural         |  **makeRigidMask.py**              |  rigidly transforms a labelmap to align with another structural image |
| Structural         |  **fs.py**                         |  convenient script for running freesurfer                             |
| -                  |  -                                 |  -                                                                    |
| Freesurfer to DWI  |  **fs2dwi.py**                     |  registers a freesurfer segmentation to a DWI                         |
| Tractography       |  **wmql.py**                       |  simple wrapper for tract_querier                                     |


The above executables are available as soft links in `pnlNipype/exec` directory as well:
    
| Soft link | Target script |
|---|---|
| fsl_eddy | ../scripts/fsl_eddy.py |
| fsl_toup_epi_eddy | ../scripts/fsl_topup_epi_eddy.py |
| masking | ../scripts/masking.py |
| nifti_align | ../scripts/align.py |
| nifti_antsApplyTransformsDWI | ../scripts/antsApplyTransformsDWI.py |
| nifti_atlas | ../scripts/atlas.py |
| nifti_bet_mask | ../scripts/bet_mask.py |
| nifti_bse | ../scripts/bse.py |
| nifti_fs | ../scripts/fs.py |
| nifti_fs2dwi | ../scripts/fs2dwi.py |
| nifti_makeRigidMask | ../scripts/makeRigidMask.py |
| nifti_wmql | ../scripts/wmql.py |
| pnl_eddy | ../scripts/pnl_eddy.py |
| pnl_epi | ../scripts/pnl_epi.py |
| ukf | ../scripts/ukf.py |


For example, to execute axis alignment script, you can do either of the following:
    
    pnlNipype/exec/nifti_align -h
    pnlNipype/scripts/align.py -h
    


# Global bashrc

If you want your terminal to have the scripts automatically discoverable and environment ready to go,
you may put the following lines in your bashrc:

    source ~/miniconda3/bin/activate            # should intoduce '(base)' in front of each line
    export FSLDIR=~/fsl                         # you may specify another directory where FreeSurfer is installed
    export PATH=$PATH:$FSLDIR/bin
    source $FSLDIR/etc/fslconf/fsl.sh
    export FREESURFER_HOME=~/freesurfer         # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export $PATH=$PATH:/absolute/path/to/pnlNipype/scripts
    export ANTSPATH=/path/to/ANTs/bin/
    export PATH=$ANTSPATH:ANTs/Scripts:$PATH    # define ANTSPATH and export ANTs scripts in your path
    export PATH=~/dcm2niix/build/bin

# Documentation

See the [Tutorial](TUTORIAL.md) for workflow and function of each script.


# Support

Create an issue at https://github.com/pnlbwh/pnlNipype/issues . We shall get back to you as early as possible.

