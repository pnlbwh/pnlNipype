![](Misc/pnl-bwh-hms.png)

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.3258854.svg)](https://doi.org/10.5281/zenodo.3258854) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64-orange.svg)]()

Developed by Tashrif Billah, Sylvain Bouix, and Yogesh Rathi, Brigham and Women's Hospital (Harvard Medical School).


Table of Contents
=================



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



# Dependencies:

* ANTs == 2.3.0
* freesurfer >= 5.0.3 
* FSL >= 5.0.3
* python >= 3


# Installation

## 1. Install prerequisites

Python 3, FreeSurfer>=5.0.3 and FSL>=5.0.11 (ignore the one(s) you have already):

### Check system architecture

    uname -a # check if 32 or 64 bit

### Python 3

Download [Miniconda Python 3.6 bash installer](https://conda.io/miniconda.html) (32/64-bit based on your environment):
    
    sh Miniconda3-latest-Linux-x86_64.sh -b # -b flag is for license agreement

Activate the conda environment:

    source ~/miniconda3/bin/activate # should introduce '(base)' in front of each line

### FreeSurfer
    
Follow the [instruction](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) to download and install FreeSurfer >= 5.0.3
After installation, you can check FreeSurfer version by typing `freesurfer` on the terminal.


### FSL

Follow the [instruction](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation) to download and install FSL.


### ANTs

You can build ANTs from [source](https://github.com/ANTsX/ANTs). Additionally, you should define [ANTSPATH](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS#set-path-and-antspath)




## 2. Install pipeline

Now that you have installed the prerequisite software, you are ready to install the pipeline:

    git clone https://github.com/pnlbwh/pnlNypipe.git && cd pnlNypipe
    pip install -r requirements.txt


## 3. Configure your environment

    source ~/miniconda3/bin/activate           # should introduce '(base)' in front of each line
    export FSLDIR=~/fsl/                       # setup fsl environment
    source $FSLDIR/etc/fslconf/fsl.sh
    export PATH=$PATH:$FSLDIR/bin
    export FREESURFER_HOME=~/freesurfer        # you may specify another directory where FreeSurfer is installed
    source $FREESURFER_HOME/SetUpFreeSurfer.sh
    export ANTSPATH=/path/to/ANTs/bin/
    export PATH=$ANTSPATH:ANTs/Scripts:$PATH   # define ANTSPATH and export ANTs scripts in your path

*(If you would like, you may edit your [bashrc](#global-bashrc) to have environment automatically setup
every time you open a new terminal)*

## 3. Tests

### i. Preliminary

Upon successful installation, you should be able to see help message of each script in the pipeline:
    
    cd lib
    ./atlas.py --help
    ./fs2dwi.py --help
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
     
     
You may specify `N_PROC` parameter in `lib/util.py` for default number of processes to be used across scripts in the pipeline.

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

You can call any these scripts directly, e.g.

    scripts/bse.py -h


It's important to note that usually the scripts are calling other binaries, such
as those in *ANTS*, *FreeSurfer* and *FSL*. So, make sure you source each of their environments 
so individual scripts are able to find them.

This table summarizes the scripts in `pnlNipype/scripts/`:

| Category           |  Script                            |  Function                                                             |
|--------------------|------------------------------------|-----------------------------------------------------------------------|
| General            |  **niftiAlign.py**                 |  axis aligns and centers an image                                     |
| General            |  **bet_mask.py**                   |  masks a 3D/4D MRI using FSL bet                                      |
| General            |  **masking.py**                    |  skullstrips by applying a labelmap mask                              |
| -                  |  -                                 |  -                                                                    |
| DWI                |  **antsApplyTransformsDWI.py**     |  applies a transform to a DWI                                         |
| DWI                |  **bse.py**                        |  extracts a baseline b0 image                                         |
| -                  |  -                                 |  -                                                                    |
| DWI                |  **pnl_epi.py**                    |  corrects EPI distortion via registration                             |
| DWI                |  **fsl_toup_epi_eddy.py**          |  corrects EPI distortion using FSL topup and eddy_openmp              |
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





### Global bashrc

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
    export PATH=$ANTSPATH:ANTs/Scripts:$PATH   # define ANTSPATH and export ANTs scripts in your path


# Documentation

See the [Tutorial](TUTORIAL.md) for workflow and function of each script.


## Support

Create an issue at https://github.com/pnlbwh/pnlNipype/issues . We shall get back to you as early as possible.

