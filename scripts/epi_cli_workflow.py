#!/usr/bin/env python

from nipype import Node, Function, Workflow, SelectFiles
from nipype.interfaces import DataSink
from conversion import read_cases
from os.path import join as pjoin, isdir
from os import makedirs
from shutil import rmtree

# ============================================================================================================
parent_directory= '/tmp/dwi_pipeline'
output_base_dir= pjoin(parent_directory, 'derivatives/tmp')
if isdir(parent_directory):
    rmtree(parent_directory)
makedirs(output_base_dir)

input_base_directory= '/home/tb571/Downloads/INTRuST_BIDS_1/'
cases= read_cases(pjoin(input_base_directory, 'caselist.txt'))


# ============================================================================================================
def intermediate_outputs_wf(input_file_name):
    from os.path import join as pjoin, basename

    prefix = basename(input_file_name).split('.')[0]
    parent_directory = '/tmp/dwi_pipeline'
    output_base_dir = pjoin(parent_directory, 'derivatives/tmp')
    outPrefix = pjoin(output_base_dir, prefix)

    align_prefix = outPrefix + '-xc'
    eddy_prefix = outPrefix + '-eddy'
    epi_prefix = outPrefix + '-epi'
    bse_output = outPrefix + '-bse'
    bet_prefix = outPrefix
    ukf_output = outPrefix
    
    t2_align_prefix = outPrefix.replace('_dwi','_T2w')+'-xc'

    t1MaskCsv = '/home/tb571/Downloads/pnlpipe/soft_light/trainingDataT1AHCC-8141805/trainingDataT1Masks-hdr.csv'

    return (align_prefix, eddy_prefix, epi_prefix, bse_output, bet_prefix, ukf_output, t2_align_prefix, t1MaskCsv)

def_inter_node= Node(Function(input_names=['input_file_name'],
                output_names= ['align_prefix', 'eddy_prefix', 'epi_prefix', 'bse_output', 'bet_prefix', 'ukf_output',
                't2_align_prefix', 't1MaskCsv'], function= intermediate_outputs_wf), name='def_inter_outputs')


# ============================================================================================================
templates = {'t1w': 'sub-{subject}/anat/*T1w.nii.gz',
             't2w': 'sub-{subject}/anat/*T2w.nii.gz',
             'dwi': 'sub-{subject}/dwi/*dwi.nii.gz',
             'bvalFile': 'sub-{subject}/dwi/*dwi.bval',
             'bvecFile': 'sub-{subject}/dwi/*dwi.bvec'}

select_files= Node(SelectFiles(templates, base_directory= input_base_directory), name= 'select_files')
select_files.iterables = [('subject', ['003_GNX_021'])]
# select_files.iterables = [('subject', cases)]



# ============================================================================================================
data_sink = Node(DataSink(base_directory=pjoin(parent_directory, 'derivatives')), name='datasink')



# ============================================================================================================
from interfaces import Align, Eddy, Bse, Mask, Ukf, TrainingMask, Epi, Wmql

eddy_pipeline= Workflow(name='eddy_pipeline', base_dir= parent_directory)

align_node= Node(Align(), name='axis_align_center')
eddy_node= Node(Eddy(), name='eddy_correct')
bse_node= Node(Bse(), name='baseline_img')
mask_node= Node(Mask(), name='bet_mask')
ukf_node= Node(Ukf(), name='UKFTractography')
eddy_pipeline.connect([(select_files, def_inter_node, [('dwi', 'input_file_name')]),
                       (def_inter_node, align_node, [('align_prefix','out_prefix')]),
                       (def_inter_node, eddy_node, [('eddy_prefix','out_prefix')]),
                       (select_files, align_node,[('dwi','in_img'), ('bvalFile','in_bval'), ('bvecFile','in_bvec')]),
                       (align_node, eddy_node, [('out_img', 'in_img'), ('out_bval', 'in_bval'), ('out_bvec', 'in_bvec')]),
                       (eddy_node, data_sink, [('out_img', 'eddy_corrected'), ('out_bval', 'eddy_corrected.@bval'),
                                               ('out_bvec', 'eddy_corrected.@bvec')]),
                       (eddy_node, bse_node, [('out_img', 'in_img'), ('out_bval', 'in_bval')]),
                       (def_inter_node, bse_node, [('bse_output','bse_img')]),
                       (bse_node, mask_node, [('out_img','in_img')]),
                       (def_inter_node, mask_node, [('bet_prefix','out_prefix')]),
                       (mask_node, ukf_node, [('out_img','in_mask')]),
                       (eddy_node, ukf_node, [('out_img','in_img')]),
                       (def_inter_node, ukf_node, [('ukf_output','tract_file')]),
                       (eddy_node, ukf_node, [('out_bval','in_bval'), ('out_bvec','in_bvec')]),
                       (ukf_node, data_sink, [('out_tract', 'eddy_corrected.@tracts')])
                       ])


eddy_pipeline.write_graph('eddy_pipeline.dot', graph2use='flat')

# eddy_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
eddy_pipeline.run()


# ============================================================================================================
epi_pipeline= Workflow(name='epi_pipeline', base_dir= parent_directory)

t2_align_node= Node(Align(), name='t2_axis_align_center')
t2_mask_node= Node(TrainingMask(), name='structural_mask')
epi_node= Node(Epi(), name='epi_correct')
epi_ukf_node= Node(Ukf(), name='UKFTractography')
epi_pipeline.connect([(eddy_pipeline, epi_node, [('eddy_correct.out_img','dwi_img'),
                                                 ('eddy_correct.out_bval','in_bval'),
                                                 ('eddy_correct.out_bvec','in_bvec'),
                                                 ('baseline_img.out_img','bse_img'),
                                                 ('bet_mask.out_img','dwi_mask')
                                                ]),
                      (def_inter_node, epi_node, [('epi_prefix','out_prefix')]),
                      (t2_align_node, epi_node, [('out_img','t2_img')]),
                      (t2_align_node, t2_mask_node, [('out_img','in_img')]),
                      (t2_mask_node, epi_node, [('out_mask','t2_mask')]),
                      (def_inter_node, t2_align_node, [('t2_align_prefix','out_prefix')]),
                      (def_inter_node, t2_mask_node, [('t2_align_prefix','out_prefix')]),
                      (def_inter_node, t2_mask_node, [('t1MaskCsv','csvFile')]),
                      (select_files, t2_align_node,[('t2w','in_img')]),
                      (epi_node, data_sink, [('out_img', 'epi_corrected'), ('out_bval', 'epi_corrected.@bval'),
                                             ('out_bvec', 'epi_corrected.@bvec'), ('out_mask', 'epi_corrected.@mask')]),
                      (epi_node, epi_ukf_node, [('out_img','in_img'),('out_mask','in_mask')]),
                      (def_inter_node, epi_ukf_node, [('ukf_output','tract_file')]),
                      (epi_node, epi_ukf_node, [('out_bval','in_bval'), ('out_bvec','in_bvec')]),
                      (epi_ukf_node, data_sink, [('out_tract', 'epi_corrected.@tracts')])
                      ])


epi_pipeline.write_graph('epi_pipeline.dot', graph2use='flat')

# epi_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
epi_pipeline.run()

