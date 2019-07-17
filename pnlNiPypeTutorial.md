This manual goes step by step through the processes involved in the PNL’s core image-processing pipeline with .nii. The goal of this tutorial is to teach new lab members and students the steps of the semi-automated, standardized processing pipeline seen below.

**Important notes**
Before you start this tutorial, here is some helpful advice:
1. Think before you type.
2. With great power comes great responsibility.

And here are some things to keep in mind as you go through this tutorial
* These characters "<>" indicate something that you enter yourself, such as `<yourusernamehere>`
* Whenever you're running a script, you can often type `<nameofscript> -h` or `<nameofscript> --help` to get more information about it. 
* Don't hit enter unless you're sure what you've typed is correct and that it will do what you want it to do. 

**NOTE:** this manual is not an exhaustive overview of the different image processing techniques that the PNL utilizes, and does not include instructions for manual segmentation, manual WM tract delineation, TBSS, NODDI, etc.)*

**Set up sample files**

The pipeline relies heavily on the use of the Linux operating system, which unlike Microsoft Windows or Mac OS X, is text and terminal based.  It is best to gain some familiarity with Linux (with a Linux tutorial) before beginning this pipeline tutorial. However, all the steps used in Linux will be explained along the way. 

If you haven’t worked with Linux before, it’s important to know that spacing, capitalization, and typos all matter when inputting commands. If one of the scripts associated with the pipeline gives you an error message when you try to run it, it may be because of one of these things, so this is always the first place to look when figuring out the issue.

If you have questions at any point, ask an RA! They will be more than happy to help you out, and might teach you a neat trick/shortcut along the way.

In order to practice each step in the pipeline, we will use a sample case located in `/rfanfs/pnl-zorro/Tutorial/Case01183_NiPype/raw`

**Copying the Sample Case to your Home Directory**

Before beginning this tutorial, you will need to copy the directory with the sample case in it into a directory in your own “home” directory.

After logging into your account on a lab computer, go to the **Applications** drop-down menu > **System Tools** > **Terminal** to open the Linux terminal
 
Before we begin, we’ll need to make sure that your bashrc is sourced. Type: 
 ```shell
 echo source /rfanfs/pnl-zorro/software/pnlpipe3/bashrc3 >> ~/.bashrc
 source ~/.bashrc
 ```
 
  
If you don’t already have a directory in the lab’s home directory you will need to make one. Enter:
```shell
cd /rfanfs/pnl-zorro/home
```

* To make your own directory enter
  ```shell
  mkdir <yourusername>
  ```
    
Then, enter your directory and make a directory to store all your tutorial files
```shell
cd /rfanfs/pnl-zorro/home/<yourusername>
mkdir PipelineTraining
```

To copy the sample case into this PipelineTraining directory, enter:
```shell
cp –r /rfanfs/pnl-zorro/Tutorial/Case01183/raw/* /rfanfs/pnl-zorro/home/yourdirectory/PipelineTraining
```

In your **PipelineTraining** directory you should now find 3 files and 4 directories.  It is the 4 directories (Diffusion_b3000, T1, T2, and Other) that you care about, and you are now ready to begin the pipeline.

In general, there are two types of neuroimaging data that you will be working with: **diffusion** imaging data and **structural** imaging data.  As you can see from the above figure, some steps of the pipeline are shared for both structural and diffusion data, and some are unique to one type of data. Furthermore, processing structural and diffusion data require different scripts and different use of the Slicer software. This tutorial will first go through structural data processing, and then diffusion data analysis.


**The Pipeline - Structural**

**Dicom to Nifti (.nii) Conversion**

Make a new directory in PipelineTraining for structural data processing by going back into **PipelineTraining** and entering `mkdir strct`.

Processing a structural image involves processing both T1 and T2 images, which are similar images of the brain, but with differing contrasts.  

We convert structural images from their raw forms (i.e. Dicoms, Bruker) to .nii files, as these are most compatible with our processing pipeline. In order to convert structural dicoms to .nii file, use the command
```shell
dcm2niix -b y -z y -f <file name> -o <output directory> <dicom directory>
```

Make sure that you are in the PipelineTraining directory and then enter:
```shell
dcm2niix -b y -z y -f sample_T1 -o strct/ T1/
```
Once this is completed, enter:
```shell
dcm2niix -b y -z y -f sample_T2 -o strct/ T2/
```
The files `sample_T1.nii` and `sample_T2.nii` should now be in your `strct` directory, which you can see if you enter `ls` while in that directory

 * **Note:** `dcm2niix` can also be used to convert to `nrrd` files.

  * If you want to convert to a `nrrd` (specifically, an `nii.gz` and a `raw.gz` file), use the `-e` flag. For example, `dcm2niix -b y -z y -e y -f sample_T1 -o strct/ T1/`.

•	In order to save space on the system, best practice is to zip the DICOM directory after you have converted it. To do this enter:
`tar -cf <DICOM directory.tar>  <DICOM directory>`. If you ever want to use the files again you can simply unzip the files by entering `tar -xvf <.tar file>`.

**Axis Align and Centering**

The next step in the pipeline centers the images and aligns them on the x-y-z axis, in order to standardize the position and orientation of each image in space.

`cd` to the directory with your structural `.nii` files (`strct`)

The command for axis aligning images is `nifti_align –-axisAlign --center -i <input file> -o <output file>`

For your images, enter:
```shell
nifti_align –-axisAlign –-center –i sample_T1.nii.gz –o sample_T1-xc.
```

Next enter:
```shell
 nifti_align –-axisAlign –-center –i sample_T2.nii.gz –o sample_T2-xc
```

The files `sample_T1-xc.nii.gz` and `sample_T2-xc.nii.gz` will now be in that directory as well, and will be axis aligned and centered.

Now that you have the axis aligned and centered image, you don’t have any use for older versions of the files. To remove some unnecessary files, enter `rm *.json` in the strct directory. This removes an artifact of the conversion from `DICOM` to `nii.gz`.

* **Note:** REMOVING FILES USING RM IS A PERMANENT ACTION AND IF YOU REMOVE FILES THAT YOU NEED, THEY ARE **GONE**. Because of this be very careful when you remove files and only remove and only remove files that you are 100% sure you and nobody else will ever need again. If you don’t know what it is, do not remove it. Also, as a good rule of thumb it is best to never remove files that you did not make because you never know what they could be being used for. Basically, the only files we ever remove are ones that are redundant, such as in the example above.

Right now you are only practicing on a single case, but often you will want to axis align and center many cases at once.  You can save a lot of time by using a `for` loop in the shell, so when you eventually find yourself in this situation, ask someone to show you how these work.
Example for loop:
```shell
for i in *.nii.gz; do
  command 1;
  command 2;
done
```

**Quality Control (Parameter and Visual)**

After you axis align and center the structural images, you need to check the quality of the images themselves (visual), and the parameters used to acquire the images (parameter). Quality checking every image is crucial to ensure that we are only analyzing good data. Parameters are checked from the image header in the terminal, and the images themselves are checked in `Slicer`.

* **Note:** Whether or not each case passes or fails QC should be recorded in an Excel spread sheet on **LabArchives**.

When checking the image parameters, it is helpful to know what the header should be (ask your PI). We are looking for consistency in the headers between all cases. 

In order to check the image header, use `fslhd`. For your case, enter:
```shell
fslhd sample_T1-xc.nii.gz
```
After you have finished checking the T1, you must also check the T2.  For this example, you can enter:
```shell
fslhd sample_T2-xc.nii.gz
```

There are several fields that you will need to check in the image header. Bear in mind that, unless otherwise specified, the value for each field listed is the value that you should see in this example, but it may vary depending on your project. 

1. First, the `sform_{x,y,z}` parameters should read `Left-to_Right`, `Posterior-to-Anterior`, and `Inferior-to-Superior` for both T1 and T2. (If it does not, it will likely read `right-anterior-superior`). Talk to someone about if you need to change this. The space should be consistent in all cases.

2. Next, `dim 1`, `dim 2`, and `dim 3` (image sizes) should always be the same between all cases in your dataset.  Any case with incorrect sizes automatically fails and can no longer be used for further processing. In this sample case `dim1`, `dim2`, and `dim3` should read `256 256 176` for T1 and T2.

3. `sto_xy{1,2,3,4}` (space directions and space origins) should be the same between cases. Small deviations in space directions between cases are okay (e.g. .98877350 instead of 1), but a large difference (e.g. 2 instead of 1) is a problem, as is a difference in sign (e.g. -1 instead of 1). Depending on the situation, the space directions of an image may be corrected via upsampling or downsampling the image. Talk to an RA or your PI about this possibility if you encounter, it. In this example it should read `(1,0,0,-127.5) (0,1,0,-127.5) (0,0,1,-87.5) (0, 0, 0, 1)` for T1 and T2. If a case has a different space origin, it may mean that this case was not axis aligned and centered.

   * Many of these fields can also be compared between all cases at once by using a `for` loop and `| grep`.

In addition to checking the image header, you need to do a visual QC of the images with **Slicer**. If you are not familiar with Slicer, there is a separate tutorial for Slicer How-To.

Before you start QCing your actual data, ask a Research Assistant for a QC tutorial! They can teach you what problems to look for in your structural images.

* To open Slicer, enter:
```shell
/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer
```

* To open your sample file go to **File** > **Add Data** > **Choose Files to Add** and then open `sample_T1-xc.nii.gz` in the `/rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct` directory. 

* Now that you have the file open, you will want to turn off the interpolation that Slicer automatically does. To do this go to the colored bar of one of the viewing windows and hover over the tack icon. On the bar that drops down, click the rings, which are next to the double chevrons. This will make any changes happen in all of the windows. Then click the double chevrons to get the rest of the menu and click on the button in the bottom row called **Interpolate background** next to the bar containing the filename. This will make the image look more pixelated, but we want interpolation off because it can hide some of the artifacts you are looking for.

* You will want to examine your images for various potential artifacts and issues, e.g. **motion artifacts**, **ringing**, **ghosting of the skull or eyeballs**, **cut-offs and other artifacts**. If you see any of these problems in the scan, note it in your QC spreadsheet. Be sure to also check with your PI about what qualifies as a failed scan for your dataset.

* Be sure to QC both your T1 and your T2 images (`sample_T2-xc.nii.gz`)

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/motion_vs_normal.png" width="70%">
An example of a severe motion artifact (A) compared with a good image (B).
<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/ghosting.png" width="70%">

An example of ghosting where you can see the back of the skull is shown a second time in the middle of the brain.

Example of ringing. If you look closely at the top of the image you will see ringing forming around the outside of the brain (which has been magnified below)

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/ringing.png" width="70%">

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/ringing_closeup.png" width="70%">


**Brain Masking and Mask QC**

The next step in the pipeline involves making a “mask” for your structural data in order to define what is brain and what is not brain in the image. Structural masking is very important for other processing, especially for getting good Freesurfer output, and for accurate registration of brain images.

You will create brain masks for your data by using a training data set consisting of previously created and edited masks. We typically use T2 images (if you have acquired these) to make masks for both T2 and T1 images. There is a default training set that we use, however depending on your dataset you may need to create your own training data (e.g., if you are imaging children)

First, make sure you are in the `strct` directory in your `PipelineTraining` directory. Make a new directory called `TrainingData`.

Next, you need to create a `.csv` file in this TrainingData directory, that points to the training cases and training masks we will use. In this example you can enter:
```shell
cd /rfanfs/pnl-zorro/software/pnlutil/trainingDataT2Masks
```

Once in this directory, enter:
```shell
./mktrainingfiles.sh /rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct/TrainingData
```
This will make a usable file for the masking script in your directory. You should now be able to see that `trainingDataT2Masks.csv` exists in `<yourdirectory>/PipelineTraining/strct/TrainingData`.

`cd` to your `strct` directory and enter:
```shell
nifti_atlas csv /rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct/TrainingData/trainingDataT2Masks.csv –i sample_T2-xc.nii.gz –o sample_T2-mask
```
This command will generate a mask for your T2 image, however it takes several hours to finish running.

* Because `nifti_atlas` takes so long to run, we have saved you the trouble of having to wait for the script to finish on your data. Instead, you can find an already generated sample T2 mask for your data in the `Other` directory in `PipelineTraining`. The file is called `sample_T2-mask.nii.gz` and has an accompanying raw file.
* Now you can enter control+c into the terminal to stop the `nifti_atlas` script, and you can copy the mask file into your `strct` directory for use in further processing.

•	In addition to the brief overview of masking laid out below, there is also a manual dedicated just to masking that you can take a look at. It is a little outdated because it uses an older version of 3D Slicer, but the main part about how to edit structural masks effectively continues to be relevant. You should pay particular attention to the section “Initial Editing” through “Reviewing the Mask”. You don’t have to do it how the maker of the manual does it exactly, but she offers many helpful pieces of advice:

[Link to the Manual Here](https://drive.google.com/file/d/0B_CbEBeE5Vr0SEwyS0RNWlJLbWs/view?usp=sharing)

After you run `nifti_atlas`, you need to check the quality of your mask. Open **Slicer** by entering `/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer`.

Open `sample_T2-mask.nii.gz` in **Slicer**, which should be in your `strct` directory.  Make sure that the **Label Map** option is selected under **Show Options** before opening it. You will also need to open `sample_T2-xc.nii.gz`.

You’ll need to convert the mask to a segmentation. Go to the “Segmentations” module, and go to “Export/import models and labelmaps.” Make sure “Import” and “Labelmap” are highlighted, and that your mask is the “Input node.” Click **Import**.

Switch to the **“Segment Editor”** module. Click on the “Sample_T2-mask”, and make sure the segmentation is “mask” and the master volume is “sample_T2-xc”. 

Because they use training data to make the masks, structural masks often do not need a lot or any editing. You should mainly edit large chunk of brain that are missing or large areas that are labeled that are not brain. Since it would be near impossible to be consistent, do not worry about editing single voxels around the edge of the brain. Sometimes this can be more harmful than beneficial, but on this example brain there are a few places that could use editing.

You now have a set of tools before you on the left portion of the screen that you can use to make sure that all of the brain and only brain is covered by the mask, although it is best to be over-inclusive as opposed to under inclusive. I’ve found it’s best to start by selecting the **Margin** tool, which is the second one in the second row under **Effects**. Make sure “Grow” is selected and then choose **Apply** as this will make sure the edges are covered.

The tool that is mainly useful for editing the mask is the **Paint** tool, which is the second tool in the first row. Also feel free to experiment with the other tools to see if you can make good use of them  

* At this point your mouse will have a circle around it that shows the current size of your brush. There are a couple of things you should be aware of when using this tool to make your life easier:

  * Turn on **Toggle crosshair** which is the orange crosshair button above the red bar. With this on, whenever you are in one of the views and hit the **Shift** key, you will see what that location looks like on the other two slice views as well

  * If you hover over the tack icon at the top left corner of each view in the colored bar, another bar will drop down and on that you will want to select **Link/unlink the slice controls (except scales) across all Slice Viewers** as this will make it so that any changes made will happen in all views

  * If you then hover over the double chevrons next to the **Link/unlink** toggle, the menu will drop down further. Here you can lower the opacity of the mask by changing the number next to **sample-dwi-tensor-mask**. I usually like **0.6**. 

  * You’ll notice that next to the opacity control on the right is the **Toggle between showing label map volume with regions outlined or filled**. As it sounds like this toggles whether you see the whole mask or just the outline and this can sometimes be useful.

  * Two rows below the outline toggle is the **Interpolate background** toggle and it is often easiest to use the pixelated option, although both are useful in some situations.

  * There are also a number of things that can be done using the keyboard, but in order for these to work you have to click on of the viewing windows after you’ve selected the paint tool. 

    * Pressing the `g` key will toggle whether or not the mask is shown
    * Pressing the `3` key toggles whether you are applying or getting rid of mask.  Which setting you are on is shown on the left by the colored bar under **PaintEffect**
    * Pressing Shift and scrolling with the mouse scroll wheel. will make the brush larger and smaller
    * Pressing the `z` key will undo the last edit you made, and the `y` key will redo the last edit you made.
    * Pressing the `+` and `–` keys will make the brush larger and smaller

When masking, make sure that you go through every slice on all three viewing windows. It is typical to start with the axial view (red) and go through at least twice.  For the inferior part of the brain, we don’t begin the mast until you can see the cerebellum.  We don’t include the eyes or optic nerves as brain, and there are a bunch of structures you will see that look like they might be brain but are not, but you will learn to recognize these as you go. Be sure to ask if you are unsure to start.  Make sure before you are done that there are no single-voxel islands. The final mask should look something like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/t2mask.png" width="80%">

It might be useful for you to see a full example of a mask. Make sure you are in your PipelineTraining directory, and enter:
```shell
cp /rfanfs/pnl-zorro/software/pnlutil/trainingDataT2Masks/01063* ./
```

This will copy one of the T2 training masks and its corresponding raw file to your PipelineTraining directory. Enter ``/rfanfs/pnl-zorro/software/Slicer-4.10.1-linux-amd64/Slicer``, and open these files (`01063-t2w-mask.nii.gz` and `01063-t2w.nii.gz`) from your PipelineTraining directory (**Ctrl+o** in **Slicer**). Remember to select **“Labelmap”** for the mask!

  * Scroll through the mask to get a sense of what is and isn’t brain. It might take awhile to get comfortable, and that’s okay! Remember, you can always ask questions and ask for help. These will always be in your PipelineTraining directory, so if you ever want to look back and refer to some sample masks while you’re working on a project, feel free to do so.

To turn the mask back into a labelmap, go back to the **Segmentations** module. Go back to “Export/import models and labelmaps.” Make sure “Export” and “Labelmap” are highlighted, and that your mask is the “Output node.” Click **Export**. Make sure to save your mask with **Ctrl+s**, and make sure that you know the path of where you’re saving it to.

**FreeSurfer Segmentation and QC**

Now that you have a good mask on your T2, you are going to apply that mask to your T1 image and generate an automated label map for white and gray matter parcellation. 

You will now need to complete an additional step so that the T2 mask you just made is aligned in the same way that the T1 is because you are about to register the T2 mask onto the T1 image. When you are in your `strct` directory, enter:
```shell
nifti_makeRigidMask -l sample_T2-mask.nii.gz -i sample_T2-xc.nii.gz -t sample_T1-xc.nii.gz -o sample_T1-mask.nii.gz
```

  * The `-l` flag is the labelmap that you’re moving to another image.
  * The `-i` flag is the input T2 .nii.gz image
  * The `-t` flag is the target image for which you want the new mask.
  * The `-o` flag is the output mask that will be generated.

There are a lot of settings that FreeSurfer has available for you to adjust what you want to do, but often times in this lab we use a standard set of settings which have been automated in a script called `nifti_fs`. Enter:
```shell
nifti_fs –i sample_T1-xc.nii.gz –m sample_T1-mask.nii.gz –o sample_freesurfer
```
This process will take about 12 hours to run to completion for each case.

  * `sample_freesurfer` can also be found in the `Other` directory as part of your `PipelineTraining` directory. Stop **FreeSurfer** from running by entering **Control+c** and you can copy this directory into strct. Just remember to use the `-r` option here since there are many directories and files within this

Once it has completed, you need to quality control your FreeSurfer labelmap. To start that you will need to start by opening it in Slicer. Enter:
`/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer`to open slicer and then open it going to **File** > **Add Data** > **Choose File** to Add then go to your `sample_freesurfer` directory in strct and then go into `mri` and open `wmparc.mgz`. Before selecting the final **OK** make sure you select **Show Options** and then select **LabelMap**. Also open `brain.mgz`, which can be found in the `sample_freesurfer/mri directory`.

Now in order to actually see your label map transposed on the T1, you need to go to the **Modules** drop-down menu and select **Volumes**. First, make sure the Active Volume is `wmparc`. Then, under the **Volume Information** heading, make sure LabelMap is selected. Last, under the Display heading, for the **Lookup Table** dropdown box, go to **FreeSurfer** > **FreeSurferLabels**. You should end up with something that looks like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/good_fs.png" width="80%">

The first thing to look for that will be immediately obvious is whether the label map and the T1 image are aligned in the same way. The easiest way to do many of these checks is to reduce the opacity of the label map in the same way that you did with the masks you’ve made.

Next you will want to scroll through all of the slices of the brain and check if major portions of brain are missing anywhere. FreeSurfer does tend to be a little under inclusive with the cortical gray matter but that is considered okay. Here are a few examples of brains that were bad enough that they failed the check due to large missing chunks:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/fs_fail_1.png" width="50%">
<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/fs_fail_2.png" width="50%">


Two particularly common issues are missing temporal poles (below top) and inaccurate amygdala hippocampal complex (below bottom). Often times these issues will not cause the images to fail the check but they should be recorded. If these are areas that are of interest in the study you are working on, you will need to discuss with your PI how to address this. Below the areas that should be covered are outlined in red:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/inacc_amyg_hipp_fs.png" width="50%">

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/inacc_temp_pole_fs.png" width="50%">


Some useful information can be gained just from looking at the FreeSurfer output. To look at it go into the `stats` directory in `sample_freesurfer` and look at the files `aseg.stats` and `wmparc.stats` using the command `cat`.



**The Pipeline - Diffusion**

**Dicom to Nifti File Conversion**

In your `PipelineTraining` directory, enter:
```shell
dcm2niix -b y -z y -f sample_dwi -o ./ ./Diffusion_B3000
```

After a bit of a wait you will get a bunch of text to your screen but you don’t need to worry about that and you will now have a file called `sample-dwi.nii.gz` in your `Diffusion_b3000` directory (along with `sample_dwi.bval`, `sample_dwi.bvec`, and `sample_dwi.json`), which you can see by entering `ls`.

A `.bval` file is a text file where the B-value for every gradient is listed in order separated by a space. A `.bvec` file is a text file with the x,y,z vectors of each gradient listed in order separated by a space between directions and a return between gradients. This is information you can get from the file’s header, which you can learn more about below in the **Quality Control (Parameter, Visual, and Auto)** section. 

**Axis Align and Center**

To make it so that you don’t have to write the whole file path for everything, make sure you are in the directory with your `.nii.gz` file, which should be `Diffusion_b3000`

Similarly to how you axis-aligned and centered your structural images, we’ll do the same for our diffusion images. Type:
```shell
nifti_align –axisAlign --center -i sample_dwi.nii.gz -o sample-dwi-xc –bvals sample_dwi.bval –bvecas sample_dwi.bvec.
```

Like with the structural portion, you are now done with the versions of the image prior to the axis aligned and centered one so to save space it would now be best to clean these old files. Use the `rm` command to remove `sample-dwi.nii.gz`, `sample-dwi.json`, and the associated, non-xced `.bval` and `.bvec` files.

Right now you are only doing a single case, but often you will want to do this for many cases.  You can save a lot of time by using a `for`  loop in the shell, so when you eventually find yourself in this situation, ask someone to show you how these work.


**Quality Control (Parameter, Visual, and Auto)**

You will first need to do a parameter check where you are essentially making sure all of the headers look like they should and that all the cases match each other. Whether or not each case passes the different QC checks should be recorded in an **Excel** spreadsheet on **LabArchives**. There are several fields you will need to look at but first to see the header, make sure you are still in the directory with your new `.nii.gz` files and enter:
```shell
fslhd sample-dwi-xc.nii.gz
```
Bear in mind that, unless otherwise specified, the value for each field listed is the value that you should see in this example, but it may vary depending on your project.

* First, the `sform_{x,y,z}` parameters should read `Right-to-Left`, `Posterior-to-Anterior`, and `Inferior-to-Superior`. (If it does not, it will likely read `right-anterior-superior`). Talk to someone about if you need to change this. The space should be consistent in all cases.

* Next, `dim 1`, `dim 2`, `dim 3`, and `dim 4` (image sizes) should always be the same between all cases in your dataset.  Any case with incorrect sizes automatically fails and can no longer be used for further processing. In this sample case `dim 1`, `dim 2`, `dim 3`, and `dim 4` should read `128 128 70 74`.

* `sto_xy{1,2,3,4}` (space directions and space origins) should be the same between cases. Small deviations in space directions between cases are okay (e.g. .98877350 instead of 1), but a large difference (e.g. 2 instead of 1) is a problem, as is a difference in sign (e.g. -1 instead of 1). Depending on the situation, the space directions of an image may be corrected via upsampling or downsampling the image. Talk to an RA or your PI about this possibility if you encounter it. In this example it should read (-2,0,0,127.5) (0,2,0,-127.5) (0,0,2,-69) (0, 0, 0, 1). If a case has a different space origin, it may mean that this case was not axis aligned and centered.

* If you type `cat sample-dwi-xc.bval`, you can see the b-values from all the gradients. The highest be consistent across all cases, and should be a reasonable value (usually, these tend to be between 2000-3000).

* If you type `cat sample-dwi-xc.bvec`, you can see the vectors from each gradient. There should be 73 lines and the three numbers (x,y,z vectors) for each gradient should roughly match between cases.  If either there are not all of the gradients or the numbers don’t match in a case, the case is failed.

* Many of these fields can also be compared between all cases at once using a for loop.

The other half of the QC is the visual and automatic check where you look at the images on FSLEyes.

To open FSLEyes, type `fsleyes`.

To open your sample file go to **File** > **Add from File** > and then open `sample-dwi-xc.nii.gz` in the `/rfanfs/pnl-zorro/home/yourdirectory/PipelineTraining/Diffusion_b3000` directory. 

You will want to look through all 73 gradients for a few different things: **movement artifacts**, **ghosting**, and **signal drops**.  In your spread sheet from the parameter checks, note any movement artifacts and ghostings along with which gradients show signal drops. To change gradients, scroll over the **Volumes** counter.  Then, look for **DWI Component** on the left under **Display** > **Scalar Display** and you can move through them with the arrows. Look below to see an example of each:



<img src ="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/motion_vs_normal.png" width=70%>
"http://www.diffusion-imaging.com/2015/11/a-guide-to-quantifying-head-motion-in.html"
An example of a severe motion artifact (A) compared with a good image (B).

<img src ="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/ghosting.png" width=70%>
An example of ghosting where you can see the back of the skull is shown a second time in the middle of the brain.

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/signal_drop.png" width=70%>
"http://journal.frontiersin.org/article/10.3389/fninf.2014.00004/full"
An example of a signal drop.

Before turning now to the automated QC tool, check with your PI about how severe these different things need to be to disqualify a case and in the case of dropped signal, check also if you will be getting rid of gradients within a case that have dropped signal or if you will keep them.


**DIFFQC TOOL**


**Motion and Eddy Current Correction**

Now that you ideally have only the cases and gradients that are usable for further processing (which we’ll say is all of them in this example), you can correct for motion and eddy currents. Make sure you are still in the `Diffusion_b3000 directory` and enter:
```shell
pnl_eddy --bvals sample-dwi-xc.bval --bvecs sample-dwi-xc.bvec -i sample-dwi-xc.nii.gz -o sample-dwi-Ed
```
Running this to completion could take some time (about 30 minutes) and you will see it progress through each gradient. After it is done you will have a file called `sample-dwi-Ed.nii.gz` in the directory as well.

Since this takes a long time, it is also available to be copied from the `Other` directory, into your `Diffusion_b3000` directory.

**Tensor Mask**

To mask a diffusion image, follow the instructions [here](https://confluence.partners.org/pages/viewpage.action?spaceKey=PNL&title=Segment+Editor+Diffusion+Masking) to mask `sample-dwi-Ed.nii.gz` (in the `Diffusion_b3000` directory)

**EPI correction**

To further correct for distortions caused by magnet interactions and magnetic inhomogeneity (which leads to intensity loss and voxel shifts), you will now have to run an EPI correction. This is done by co-registering it with the T2 image, which means that you need to have T2 images for the case to do this step and also that you will need to have masked the T2 file (step 5 of the structural pipeline) so that you can use it for this. If T2 images were not taken for the particular case (they were for this example) then you will have to skip this step. 

You first need to skull strip the T2 image using the mask for it and to do this you need to make sure you are in the `strct` directory and then enter:
```shell
unu 2op x sample_T2-mask.nii.gz sample_T2-xc.nii.gz -o sample_T2-masked.nii.gz
```
After this `sample_T2-masked.nii.gz` will now be in your `strct` directory as well.

Now out in `PipelineTraining`, enter:
```shell
pnl_epi Diffusion_b3000/sample-dwi-Ed.nii.gz Diffusion_b3000/sample-dwi-tensor-mask.nii.gz strct/sample_T2-masked.nii.gz strct/sample_T2-mask.nii.gz Diffusion_b3000/sample-dwi-epi.nii.gz
```

* Since this takes a long time this is also available to be copied from the `Other` directory. Just be sure to copy both the `.nii.gz` and `.raw.gz` files for `sample-dwi-epi`

* If this is the first case that you are doing in a data set, and for this tutorial we can pretend that it is, you should check the glyphs of the case’s DTI because sometimes they are incorrect, which will lead to the tractography being incorrect as well.

* Even if you know little about how the glyphs should look there is an easy trick that is generally good enough when making this determination. This involves looking at the corpus callosum, which is the most major white matter bundle connecting the two hemispheres.

* Open Slicer using `/rfanfs/pnl-zorro/software/Slicer-4.10.1-linux-amd64/Slicer` and open `sample-dwi-epi.nii.gz`. The first thing you need to do is generate a DTI (Diffusion Tensor Image). This will show the orientation of the fibers in each voxel using color coding (red is left to right, blue is up and down, and green is forward to backward). Under Modules, go to **Diffusion** > **Diffusion Weighted Images** > **DWI to DTI Estimation**.

  * For **Input DWI Volume**, select sample-dwi-epi.
  * For **Output DTI Volume**, you can create a new volume as **sample-dti**.
  * For **Output Baseline Volume** you can create a new volume as **baseline**.
  * Select **Apply**.

* Going to the drop-down pin in the top left corner of a viewing window and the the double chevrons under that, you will have to change the bottom right box from the baseline to **sample-dti**. Select the rings next to the chevrons to do this for all views.  You will get an image that looks like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/dti.png" width=80%>

* Looking at the coronal view (green) scroll to a slice that has a red “U”-shape in the upper middle part of the brain. There are a lot of them, but any will do. This structure is the corpus callosum and it looks like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/dti_corpus.png" width=80%>


* Then go to the **Volumes** module and make sure that the **Active Volume** is **sample-dti**.

* Scroll down on the sidebar to the **Glyphs on Slices Display** and choose **Green** for **Slice Visibility**. Then for **Glyph Type** choose **Lines** as this will allow Slicer to run faster.

* You should now see this on your screen:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/glyph_corpus.png" width=80%>

* The area where the corpus callosum was will probably have turned to dark blue, but if it is correct the lines will follow the “u” shape to make a somewhat smooth curve. If it is incorrect, the lines will not follow the “u” shape, but instead might just all be horizontal or even form more of an “n” shape. This can be seen here:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/bad_glyph_corpus.png" width=80%>
	  
* You will also need to check the corpus callosum in the other two views (red and yellow). To do this you simply uncheck **Green** for slice visibility and select the color you want.


<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/glyph_corpus_axial.png" width=80%>

* This is how the corpus callosum should look in the in the axial view (red) if you are looking at the middle slice or thereabouts. The upper portion should be arranged like a “u” while the lower portion should be arranged like an “n”. Make sure you look at both parts of the corpus callosum because it is possible for one to be correct while the other is not:


<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/glyph_corpus_sagit.png" width=80%>
* This is how the corpus callosum should look in the sagittal view (yellow) if you are looking at around the middle slice. The glyphs should look like they are more or less arranged straight in and out parallel with your view:

* They should all look correct in this sample case, but if it doesn’t look correct, you can fix it by changing the header of the epi-corrected file. To do that, back in the terminal, enter `gedit sample-dwi-epi.nii.gz`. The header will come up in a text editor. You are interested in the **measurement frame**. The first thing you can try is changing any non-zero numbers in the first set of coordinates to negative. Then save and load the epi-corrected image in Slicer again and do the whole process over again.

If this time the glyphs look correct in the corpus callosum, you have fixed it for that case. If they still don’t look correct, change the first set of coordinates back to positive and make the second set negative. There are 7 possible permutations of negatives that you can try if necessary. It is usually the case that the proper measurement frame is the same for every case in a dataset, but this is not always the case, especially if the data was acquired on more than one scanner or over a long period of time. Because of that, before you then make this change to the header of every epi-corrected dwi for every case in the dataset, you should check this on a handful of other cases as well. 

**Two-Tensor Whole Brain Tractography**

It is now time to generate a tractography image, which creates images that look like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/tractography.png" width=80%>

In the `Diffusion_b3000` directory, make a new directory called `Tractography/`

The script that make these images works best for b-values (found in the header) where **700 <= b <= 3000**. If your b-value is not in this range, talk to your PI. Our b-value is acceptable for the current example. When you are in the `Diffusion_b3000` directory, enter:
```shell
ukf -i sample-dwi-epi.nii.gz --bvals sample-dwi-epi.bval --bvecs sample-dwi-epi.bvecs  -m sample-dwi-tensor-mask.nii.gz -o Tractography/sample-dwi-tracts.vtk --numThreads,8,--recordTensors
```
Be warned that depending on the computing power you are using this process could take anywhere from a few hours to several days.

Since this takes quite a long time this is also available to be copied from the `Other` directory. 

The value for  `--numThreads` most often is `8` and this is the computing power you are using for the process in terms of number of cores being used. For other projects you will want to ask someone how many cores you should be using.

You may also want to specify `--seedsPerVoxel`. Typically, we use `--seedsPerVoxel 10`, which means we will have 10 seed points in each voxel.  If unspecified it will use the default of 1. A higher number will cause it to take longer and lead to a larger output size, but it will generate more fibers. Ask your PI if you should use a different value. l cause there to be more fibers generated, but it will also take more time and take up more space.

Other options that can be manipulated (depending on your B-value and the number of fibers being generated) include `--minGA --minFA --seedFALimit`. 

If you want to extract free water measures from your data, make sure to also include the flags ``--freeWater --recordFreeWater``.

Once it is finished running, you can open it in slicer if you would like to see what it looks like when it is done. You will need to open `sample-dwi-tracts.vtk` in your `Tractography` directory. Be sure that before you hit **OK** you change the **Description** to **FiberBundle**.

When it opens you will notice that the whole thing is most likely pink, like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/tractography_slicer.png" width=80%>
	
There are more interesting color schemes, however, that will tell you different information about the image. You can change between these by going to the **Modules** drop down and selecting **Diffusion** > **Tractography Display**. Under the **Advanced Display** heading you can play around with the different options to look at different things. 

**Finishing the Pipeline**

To continue on from this point you will need to have both the diffusion and the structural steps completed, since these use both of them. 

**FreeSurfer labelmap to dwi-space registration**

The first step of post-processing involves registering the FreeSurfer labelmap that you made to the diffusion image since they don’t have the same resolution and aren’t in the same space. To do this make sure you are in the `PipelineTraining` directory and enter:
```shell
nifti_fs2dwi --dwi Diffusion_b3000/sample-dwi-epi.nii.gz --dwimask Diffusion_b3000/sample-dwi-epi-mask.nii.gz -f strct/sample_freesurfer witht2 --t2 strct/sample_T2-masked.nii.gz --t2mask strct/sample_T2-mask.nii.gz -o sample_fs2dwi
```
It will take about 6 hours to run to completion, so type **Ctrl+c**.

Since this takes a long time this is also available to be copied from the `Other` directory. Just be sure use the `-r` option since `sample_fs2dwi` contains lots of directories and files.

Note: If you do not have T2s as part of the case you are working with you will have to use a different version of this command, which will not lead to suboptimal but fine results. Its format is:
```shell
nifti_fs2dwi --dwi <dwi_Ed> --dwimask <tensor_mask> -f <freesurfer_directory> -o <output_directory> direct
```

Once the script has finished running, you will find that there is a file called `wmparc-in-bse.nii.gz` in the `sample_fs2dwi` directory. Open this file along with `sample-dwi-epi.nii.gz` in Slicer to see if they are registered well. Make sure that `wmparc-in-bse.nii.gz` is checked for Label Map.

When it opens, it will probably not appear as it should, and to fix this go to the **Volumes** module and for the **Active Volume** select `wmparc-in-bse`. Then, under the **Display** heading, change Lookup Table to **FreeSurfer** > **FreeSurferLabels**. It will look something like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/fs_in_dwi.png" width=80%>

To check if the registration is good you scroll through the different views similar to how you did when quality checking the FreeSurfer labelmap during step 6 of the structural portion of the pipeline. 

**White Matter Analysis**

This step is not a part of the figure on the first page of this tutorial, but it is often a good idea to complete this extra form of quality control. Note that this step makes use of something called Cluster. In order to use the cluster you need an account and a separate mini-tutorial exists to help you set this up if you need it. The purpose of doing this QC is that the tractography you produced contains thousands and thousands of fibers and it is hard to tell from looking at it if the result is reasonable.

Once you have logged into the **Cluster** and chose a free node that you will use for an interactive session by entering:
```shell
bsub -Is -XF /bin/bash
```
Note that the `-Is` stands for your interactive session and the `-XF` that you will be using graphical processing resources. If you are not running this on the Cluster using your PNL desktop, but instead No Machine, this is not applicable and you can find the information about that further down the page.

Assuming that you have already created a personal directory for yourself in the **Cluster**, you will need to copy your PipelineTraining directory into that directory in Cluster. 

* First, you will need your workstation's I.P. address. You can get this  by entering:
```shell
ip addr
```
Look for a line that looks like the following:
```shell
inet 172.23.222.249/24 brd 172.23.222.255 scope global dynamic eno1
```
In this case, the I.P. address `172.23.222.249` (ignore anything after the `/`)

Then, to copy from your workstation to the **Cluster**, you can go to your **Cluster** directory and enter:
```shell
scp -pr <yourusername>@<yourcomputer’sI.P.address>:/rfanfs/pnl-zorro/home/<yourname>/PipelineTraining ./
```
After this has completed you should now have your PipelineTraining directory in cluster as well.

Go into the `Diffusion_b3000` directory and enter:
```shell
/data/pnl/soft/whitematteranalysis/bin/wm_quality_control_tractography.py Tractography tractQC
```

It is likely that this script will not be able to run on the desktop at your PNL workstation because of graphics processing issues. If this is the case, you will have to do it instead using **NoMachine** on your personal computer, which is an app that you should have anyway because it is very useful here at the lab.

**NoMachine** will give you access to the same file system as the cluster but through a different set of servers that you can access from personal computers without taxing your machine’s processing power.

To get **NoMachine**, follow this guide on [Confluence](https://confluence.partners.org/pages/viewpage.action?spaceKey=PNL&title=Remote+Access+and+NoMachine+09.11.17)

It is also important to note that when running the white matter quality control script, it will not work if you try to log into a node like you would normally as discussed in the cluster manual. This is the only situation where you should instead just run the script without logging into a cluster node. For other jobs, even using **NoMachine**, you should still follow the typical cluster protocol.

When using No Machine for this task, since you are not logging into a node, you will also not be accessing the X-serving (by using `-XF`), but this is okay because this is automatically activated in No Machine as long as you are not logged into a node.

You will now want to copy the result of this back onto your local server. Go into your `Diffusion_b3000` directory and enter:
```shell
scp -pr tractQC <yourusername>@<yourcomputer’sI.P.address>:/rfanfs/pnl-zorro/home/<yourname>/PipelineTraining/Diffusion_b3000
```

You can now leave the **Cluster** by entering `exit` twice. Then go into your new `tractQC` directory. To do a visual QC, enter `xdg-open view_<area>.html`. There are 6 different areas that you can look at (**ant**, **inf**, **left**, **post**, **right**, and **sup**) and you should inspect each of them carefully.

* One paper that is very helpful in determining what to look for is “A diffusion tensor imaging tractography atlas for virtual in vivo dissections” (Catani & Thiebaut de Schotten, 2008) so give it a look.

Then to do a data QC, make sure you are still in the `tractQC` directory and enter:
```shell
oocalc quality_control_fibers.txt
```
A window will pop up and you can just select **OK**.

A spread sheet will then open up and in the example it will only contain one row, but normally each case will have a row. You would be mainly interested in the **TOTAL_FIBERS** and **LEN_200** columns, which count the number of total tracts and the number of the longest type of tract respectively. We are looking to see if any case has an abnormally low level of either of these values relative to the rest of the cases. The easiest way to do this would be to sort the columns and look at the lowest ones using the **Sort Ascending** or **Sort Descending** tool in the upper toolbar. 

Talk with your PI in the case where any case fails any of the QCs.

**White Matter Query Language**

At this time you will use white matter query language to put the FreeSurfer output in the same space as the tractography by using Demian’s method to automatically select fibers connecting specific regions from the whole brain tractography.

Something that would be good to do before you actually run the script is to have a look at the query files that you will have to use to reference the area you are interested in looking at. To do this go to `/projects/schiz/software/LabPython/tract_querier/queries`. Once here, enter:
```shell
gedit FreeSurfer.qry
```
and a window should pop up. Don’t change anything in this window but you’ll notice that it contains the names of all of the different brain regions followed by the number code given to them in the FreeSurfer output. When looking at a FreeSurfer labelmap, when you put your mouse over a color-coded brain region this is the number that pops up in the bottom left hand corner of the screen along with the brain region abbreviation.  If you exit out of this you can also enter:
```shell
gedit freesurfer_queries_new.qry
```
and this defines individual tracts.
 
Now go back to your PipelineTraining directory and make a new directory called **wmql**.

Now enter:
```shell
nifti_wmql -f sample_fs2dwi/wmparc-in-bse.nii.gz -i Diffusion_b3000/Tractography/sample-dwi-tracts.vtk  -q /rfanfs/pnl-zorro/software/pnlutil/pipeline/wmql-2.0.qry -o ./wmql sample
```

After it has finished running, you can go into the `wmql/` directory and see that it has generated files for all kinds of tracts.

You would now use these files to QC whichever areas you are interested in the study, so for this example we can choose a random one, say `sample_af.left.vtk`, to have a look at.  Open the file in Slicer making sure to choose **FiberBundle** option for **Description** and also open `wmparc.mgz`  in the `sample_freesurfer/mri` directory with **Volume** selected.

When it is open go to **Volumes** in **Modules** and under the **Display** header, change the **Lookup Table** value to **FreeSurferLabels**. At this point you should have something like this:

<img src="https://github.com/monicalyons/pnlNipype/blob/monicalyons-patch-1/Misc/fiber_and_fs.png" width=80%>
 
The region you are looking at with the tracts is the left arcuate fasciculus. When doing the QC the main things you want to look for are that the tracts intersect the regions they are supposed to on the label map and that they have the shape they should. A good source of this information is the Catani & Thiebaut de Schotten paper mentioned above. The region you are looking at is supposed to connect the perisylvian cortex of the frontal and temporal lobes and the example seen here does seem to do that, although as I mentioned before they should be a little off in the example.

The wm_quality_control_tractography.py script used before can also used here to do the same thing with individual tracts as long as all of the .vtk files for that tract are in the same directory.

If they are not all in the same directory to start, one way that you can do that without moving or copying all of the .vtk files is to make softlinks for them all, which is basically just a file that when accessed will redirect to the actual file. To do this you use the format:
```shell
ln -s <full path to actual file> <full path to softlink directory>.
```

**Extract Measures**

For the final step of the pipeline you need to now extract all of the measures you want from the images. There are two ways to do this:

* Way 1: Go into your `wmql/` directory. Let’s say we are still interested in the left AF. Enter:
```shell
measureTracts.py -i sample_af.left.vtk -o sample_af.left.csv
```
  * This will create a file called `sample_af.left.csv` in that directory as well.

  * You can open this file by entering:
	```shell
	oocalc sample_af.left.csv
	```

If you want to run the script on many `.vtk` files at once and have them all in the same spreadsheet, you can do this by putting all of the `.vtk` files in the same directory (or making softlinks to them in the same directory as discussed above in wmql) and replace the input with `*.vtk`.

* Way 2: In **Slicer**, you can go to the **Modules** drop-down and go to **Diffusion** > **Tractography** > **Fiber Tract Scalar Measurements**

  * Now you will need to create a blank text file for the program to put the information into. You can do this by entering in terminal `touch sample_af.txt`.

  * Under the **IO** header, for **Select Input Type**, choose **Fibers_File_Folder**. For **Fibers File Folder** select your wmql directory and for **Output Text File** you can select the text file you just made. Then for Select Output Format choose **Column_Hierarchy** and for **Output Field Separator** choose **Tab** and press **Apply**.

  * Now you can open the text file by entering `oocalc sample_af.left.txt`.

You may notice that there are some differences in what these two methods give you, so which you choose largely depends on what you’re looking for, and sometimes it may be necessary to use boths ways to get everything you need:

Way 1 will give you FA, AD, RD, and Trace among other less commonly used diffusion measures. It will give you not only the mean of these values for the case, but also the minimum and maximum values. Be careful to mind that the values it gives you are 1000 times the values you will typically see, including what you get using Way 2. This is alright but something you need to keep in mind during analyses. Way 1 will not give you FW or associated measures like FAt and so on.

Way 2 will not give you AD and RD, but it will give you FW and other measures associated with that if you record them during tractography, which Way 1 will not. Further, for FA, it will give you the measure for both tensors (since we are running two tensor tractography), as opposed to just the first tensor with Way 1. This way only gives you the mean, however, and not the min and max values. Last , this method rounds 6 digits earlier than Way 1 does.

You would normally compare different measures between cases much like you did before to see if there are any extremely low values that are possibly incorrect but obviously that is not possible with only 1 case in this example. Generally, any outliers in any field should be noted.

At this point you are ready to go into any statistical analysis that the project may require.
