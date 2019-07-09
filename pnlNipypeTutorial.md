This manual goes step by step through the processes involved in the PNL’s core image-processing pipeline with .nii. The goal of this tutorial is to teach new lab members and students the steps of the semi-automated, standardized processing pipeline seen below.

**NOTE:** this manual is not an exhaustive overview of the different image processing techniques that the PNL utilizes, and does not include instructions for manual segmentation, manual WM tract delineation, TBSS, NODDI, etc.)*

**Set up sample files**

The pipeline relies heavily on the use of the Linux operating system, which unlike Microsoft Windows or Mac OS X, is text and terminal based.  It is best to gain some familiarity with Linux (with a Linux tutorial) before beginning this pipeline tutorial. However, all the steps used in Linux will be explained along the way. 

If you haven’t worked with Linux before, it’s important to know that spacing, capitalization, and typos all matter when inputting commands. If one of the scripts associated with the pipeline gives you an error message when you try to run it, it may be because of one of these things, so this is always the first place to look when figuring out the issue.

If you have questions at any point, ask an RA! They will be more than happy to help you out, and might teach you a neat trick/shortcut along the way.

In order to practice each step in the pipeline, we will use a sample case located in `/rfanfs/pnl-zorro/Tutorial/Case01183_NiPype/raw`

**Copying the Sample Case to your Home Directory**

Before beginning this tutorial, you will need to copy the folder with the sample case in it into a folder in your own “home” directory.

After logging into your account on a lab computer, go to the **Applications** drop-down menu > **System Tools** > **Terminal** to open the Linux terminal
 
Before we begin, we’ll need to make sure that your bashrc is sourced. Type: 
 ```bash
 echo source /rfanfs/pnl-zorro/software/pnlpipe3/bashrc3 >> ~/.bashrc
 ```
  
If you don’t already have a directory in the lab’s home directory you will need to make one. Enter:
```bash
cd /rfanfs/pnl-zorro/home
```

* To make your own directory enter
  ```bash
  mkdir PipelineTraining
  ```
    
Otherwise enter your directory
```bash
cd /rfanfs/pnl-zorro/home/<yourusername>
```
To copy the sample case into this PipelineTraining directory, enter:
```bash
cp –r /rfanfs/pnl-zorro/Tutorial/Case01183/raw/* /rfanfs/pnl-zorro/home/yourdirectory/PipelineTraining
```

In your **PipelineTraining** directory you should now find 3 files and 4 directories.  It is the 4 directories (Diffusion_b3000, T1, T2, and Other) that you care about, and you are now ready to begin the pipeline.

In general, there are two types of neuroimaging data that you will be working with: **diffusion** imaging data and **structural** imaging data.  As you can see from the above figure, some steps of the pipeline are shared for both structural and diffusion data, and some are unique to one type of data. Furthermore, processing structural and diffusion data require different scripts and different use of the Slicer software. This tutorial will first go through structural data processing, and then diffusion data analysis.


**The Pipeline - Structural**

**Dicom to Nifti (.nii) Conversion**

Make a new directory in PipelineTraining for structural data processing by going back into **PipelineTraining** and entering `mkdir strct`.

Processing a structural image involves processing both T1 and T2 images, which are similar images of the brain, but with differing contrasts.  

We convert structural images from their raw forms (i.e. Dicoms, Bruker) to .nii files, as these are most compatible with our processing pipeline. In order to convert structural dicoms to .nii file, use the command `dcm2niix -b y -z y -f <file name> -o <output directory> <dicom directory>`

Make sure that you are in the PipelineTraining directory and then enter:
```bash
dcm2niix -b y -z y -f sample_T1 -o strct/ T1/
```
Once this is completed, enter:
```bash
dcm2niix -b y -z y -f sample_T2 -o strct/ T2/
```
The files `sample_T1.nii` and `sample_T2.nii` should now be in your `strct` directory, which you can see if you enter `ls` while in that directory

 * **Note:** `dcm2niix` can also be used to convert to `nrrd` files.

  * If you want to convert to a `nrrd` (specifically, an `nhdr` and a `raw.gz` file), use the `-e` flag. For example, `dcm2niix -b y -z y -e y -f sample_T1 -o strct/ T1/`.

•	In order to save space on the system, best practice is to zip the DICOM folder after you have converted it. To do this enter:
`tar -cf <DICOM directory.tar>  <DICOM directory>`. If you ever want to use the files again you can simply unzip the files by entering `tar -xvf <.tar file>`.

**Axis Align and Centering**

The next step in the pipeline centers the images and aligns them on the x-y-z axis, in order to standardize the position and orientation of each image in space.

`cd` to the directory with your structural `.nii` files (`strct`)

The command for axis aligning images is `nifti_align –-axisAlign --center -i <input file> -o <output file>`

For your images, enter:
```bash
nifti_align –-axisAlign –-center –i sample_T1.nii.gz –o sample_T1-xc. Next enter nifti_align –-axisAlign –-center –i sample_T2.nii.gz –o sample_T2-xc
```
The files `sample_T1-xc.nii.gz` and `sample_T2-xc.nii.gz` will now be in that directory as well, and will be axis aligned and centered.

Now that you have the axis aligned and centered image, you don’t have any use for older versions of the files. To remove some unnecessary files, enter `rm *.json` in the strct directory. This removes an artifact of the conversion from `DICOM` to `nii.gz`.

* **Note:** REMOVING FILES USING RM IS A PERMANENT ACTION AND IF YOU REMOVE FILES THAT YOU NEED, THEY ARE **GONE**. Because of this be very careful when you remove files and only remove and only remove files that you are 100% sure you and nobody else will ever need again. If you don’t know what it is, do not remove it. Also, as a good rule of thumb it is best to never remove files that you did not make because you never know what they could be being used for. Basically, the only files we ever remove are ones that are redundant, such as in the example above.

Right now you are only practicing on a single case, but often you will want to axis align and center many cases at once.  You can save a lot of time by using a `for` loop in the shell, so when you eventually find yourself in this situation, ask someone to show you how these work.
Example for loop:
```bash
for i in *.nrrd; do
  command 1;
  command 2;
done
```

**Quality Control (Parameter and Visual)**

After you axis align and center the structural images, you need to check the quality of the images themselves (visual), and the parameters used to acquire the images (parameter). Quality checking every image is crucial to ensure that we are only analyzing good data. Parameters are checked from the image header in the terminal, and the images themselves are checked in `Slicer`.

* **Note:** Whether or not each case passes or fails QC should be recorded in an Excel spread sheet on **LabArchives**.

When checking the image parameters, it is helpful to know what the header should be (ask your PI). We are looking for consistency in the headers between all cases. 

In order to check the image header, use `fslhd`. For your case, enter:
```bash
fslhd sample_T1-xc.nii.gz
```
After you have finished checking the T1, you must also check the T2.  For this example, you can enter:
```bash
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
```bash
/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer
```

* To open your sample file go to **File** > **Add Data** > **Choose Files to Add** and then open `sample_T1-xc.nii.gz` in the `/rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct` folder. 

* Now that you have the file open, you will want to turn off the interpolation that Slicer automatically does. To do this go to the colored bar of one of the viewing windows and hover over the tack icon. On the bar that drops down, click the rings, which are next to the double chevrons. This will make any changes happen in all of the windows. Then click the double chevrons to get the rest of the menu and click on the button in the bottom row called **Interpolate background** next to the bar containing the filename. This will make the image look more pixelated, but we want interpolation off because it can hide some of the artifacts you are looking for.

* You will want to examine your images for various potential artifacts and issues, e.g. **motion artifacts**, **ringing**, **ghosting of the skull or eyeballs**, **cut-offs and other artifacts**. If you see any of these problems in the scan, note it in your QC spreadsheet. Be sure to also check with your PI about what qualifies as a failed scan for your dataset.

* Be sure to QC both your T1 and your T2 images (`sample_T2-xc.nrrd`)


An example of a severe motion artifact (A) compared with a good image (B).

An example of ghosting where you can see the back of the skull is shown a second time in the middle of the brain.

Example of ringing. If you look closely at the top of the image you will see ringing forming around the outside of the brain (which has been magnified in the bottom left corner)



**Brain Masking and Mask QC**

The next step in the pipeline involves making a “mask” for your structural data in order to define what is brain and what is not brain in the image. Structural masking is very important for other processing, especially for getting good Freesurfer output, and for accurate registration of brain images.

You will create brain masks for your data by using a training data set consisting of previously created and edited masks. We typically use T2 images (if you have acquired these) to make masks for both T2 and T1 images. There is a default training set that we use, however depending on your dataset you may need to create your own training data (e.g., if you are imaging children)

First, make sure you are in the `strct` folder in your `PipelineTraining` directory. Make a new directory called `TrainingData`.

Next, you need to create a `.csv` file in this TrainingData directory, that points to the training cases and training masks we will use. In this example you can enter:
```bash
cd /rfanfs/pnl-zorro/software/pnlutil/trainingDataT2Masks
```

Once in this directory, enter:
```bash
./mktrainingfiles.sh /rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct/TrainingData
```
This will make a usable file for the masking script in your directory. You should now be able to see that `trainingDataT2Masks.csv` exists in `<yourdirectory>/PipelineTraining/strct/TrainingData`.

`cd` to your `strct` folder and enter:
```bash
nifti_atlas csv /rfanfs/pnl-zorro/home/<yourdirectory>/PipelineTraining/strct/TrainingData/trainingDataT2Masks.csv –i sample_T2-xc.nii.gz –o sample_T2-mask
```
This command will generate a mask for your T2 image, however it takes several hours to finish running.

* Because `nifti_atlas` takes so long to run, we have saved you the trouble of having to wait for the script to finish on your data. Instead, you can find an already generated sample T2 mask for your data in the `Other` folder in `PipelineTraining`. The file is called `sample_T2-mask.nii.gz` and has an accompanying raw file.
* Now you can enter control+c into the terminal to stop the `nifti_atlas` script, and you can copy the mask file into your `strct` folder for use in further processing.

•	In addition to the brief overview of masking laid out below, there is also a manual dedicated just to masking that you can take a look at. It is a little outdated because it uses an older version of 3D Slicer, but the main part about how to edit structural masks effectively continues to be relevant. You should pay particular attention to the section “Initial Editing” through “Reviewing the Mask”. You don’t have to do it how the maker of the manual does it exactly, but she offers many helpful pieces of advice:

[Link to the Manual Here](https://drive.google.com/file/d/0B_CbEBeE5Vr0SEwyS0RNWlJLbWs/view?usp=sharing)

After you run `nifti_atlas`, you need to check the quality of your mask. Open **Slicer** by entering `/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer`.

Open `sample_T2-mask.nii.gz` in **Slicer**, which should be in your `strct` folder.  Make sure that the **Label Map** option is selected under **Show Options** before opening it. You will also need to open `sample_T2-xc.nii.gz`.

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

When masking, make sure that you go through every slice on all three viewing windows. It is typical to start with the axial view (red) and go through at least twice.  For the inferior part of the brain, we don’t begin the mast until you can see the cerebellum.  We don’t include the eyes or optic nerves as brain, and there are a bunch of structures you will see that look like they might be brain but are not, but you will learn to recognize these as you go. Be sure to ask if you are unsure to start.  Make sure before you are done that there are no single-voxel islands. The final mask should look something like this:

It might be useful for you to see a full example of a mask. Make sure you are in your PipelineTraining directory, and enter:
```bash
cp /rfanfs/pnl-zorro/software/pnlutil/trainingDataT2Masks/01063* ./
```

This will copy one of the T2 training masks and its corresponding raw file to your PipelineTraining directory. Enter `s4`, and open these files (`01063-t2w-mask.nii.gz` and `01063-t2w.nii.gz`) from your PipelineTraining directory (**Ctrl+o** in **Slicer**). Remember to select **“Labelmap”** for the mask!

  * Scroll through the mask to get a sense of what is and isn’t brain. It might take awhile to get comfortable, and that’s okay! Remember, you can always ask questions and ask for help. These will always be in your PipelineTraining directory, so if you ever want to look back and refer to some sample masks while you’re working on a project, feel free to do so.

To turn the mask back into a labelmap, go back to the **Segmentations** module. Go back to “Export/import models and labelmaps.” Make sure “Export” and “Labelmap” are highlighted, and that your mask is the “Output node.” Click **Export**. Make sure to save your mask with **Ctrl+s**, and make sure that you know the path of where you’re saving it to.

**FreeSurfer Segmentation and QC**

Now that you have a good mask on your T2, you are going to apply that mask to your T1 image and generate an automated label map for white and gray matter parcellation. 

You will now need to complete an additional step so that the T2 mask you just made is aligned in the same way that the T1 is because you are about to register the T2 mask onto the T1 image. When you are in your `strct` folder, enter:
```bash
nifti_makeRigidMask -l sample_T2-mask.nii.gz -i sample_T2-xc.nii.gz -t sample_T1-xc.nii.gz -o sample_T1-mask.nii.gz
```

  * The `-l` flag is the labelmap that you’re moving to another image.
  * The `-i` flag is the input T2 .nii.gz image
  * The `-t` flag is the target image for which you want the new mask.
  * The `-o` flag is the output mask that will be generated.

There are a lot of settings that FreeSurfer has available for you to adjust what you want to do, but often times in this lab we use a standard set of settings which have been automated in a script called `nifti_fs`. Enter:
```bash
nifti_fs –i sample_T1-xc.nii.gz –m sample_T1-mask.nii.gz –o sample_freesurfer
```
This process will take about 12 hours to run to completion for each case.

  * `sample_freesurfer` can also be found in the `Other` folder as part of your `PipelineTraining` directory. Stop **FreeSurfer** from running by entering **Control+c** and you can copy this folder into strct. Just remember to use the `-r` option here since there are many directories and files within this

Once it has completed, you need to quality control your FreeSurfer labelmap. To start that you will need to start by opening it in Slicer. Enter:
`/rfanfs/pnl-zorro/software/Slicer-4.8.1-linux-amd64/Slicer`to open slicer and then open it going to **File** > **Add Data** > **Choose File** to Add then go to your `sample_freesurfer` folder in strct and then go into `mri` and open `wmparc.mgz`. Before selecting the final **OK** make sure you select **Show Options** and then select **LabelMap**. Also open `brain.mgz`, which can be found in the `sample_freesurfer/mri folder`.

Now in order to actually see your label map transposed on the T1, you need to go to the **Modules** drop-down menu and select **Volumes**. First, make sure the Active Volume is `wmparc`. Then, under the **Volume Information** heading, make sure LabelMap is selected. Last, under the Display heading, for the **Lookup Table** dropdown box, go to **FreeSurfer** > **FreeSurferLabels**. You should end up with something that looks like this:

The first thing to look for that will be immediately obvious is whether the label map and the T1 image are aligned in the same way. The easiest way to do many of these checks is to reduce the opacity of the label map in the same way that you did with the masks you’ve made.

Next you will want to scroll through all of the slices of the brain and check if major portions of brain are missing anywhere. FreeSurfer does tend to be a little under inclusive with the cortical gray matter but that is considered okay. Here are a few examples of brains that were bad enough that they failed the check due to large missing chunks:

Two particularly common issues are missing temporal poles (below left) and inaccurate amygdala hippocampal complex (below right). Often times these issues will not cause the images to fail the check but they should be recorded. If these are areas that are of interest in the study you are working on, you will need to discuss with your PI how to address this. Below the areas that should be covered are outlined in red:

Some useful information can be gained just from looking at the FreeSurfer output. To look at it go into the `stats` folder in `sample_freesurfer` and look at the files `aseg.stats` and `wmparc.stats` using the command `cat`.
