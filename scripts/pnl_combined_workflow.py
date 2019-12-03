#!/usr/bin/env python

from nipype import Node, Function, Workflow, SelectFiles, DataSink
from nipype.interfaces import DataSink, IdentityInterface
from conversion import read_cases
from os.path import join as pjoin, isdir
from os import makedirs
from shutil import rmtree

from script_interfaces import create_dirs, define_outputs_wf, Align, Eddy, Epi, Bse, BetMask, Masking, TrainingMask, \
    Ukf, FsSeg, Wmql, WmqlQc, Fs2Dwi


# ============================================================================================================
# define input data and output directories
bids_data_dir= '/home/tb571/Downloads/INTRuST_BIDS/'
cases= read_cases(pjoin(bids_data_dir, 'caselist.txt'))
cases=['003GNX007']
pipe_out_dir= '/tmp/dwi_pipeline'
bids_derivatives= pjoin(bids_data_dir,'derivatives','pnlNipype')
overwrite=False
if overwrite and isdir(pipe_out_dir):
    rmtree(pipe_out_dir)
    rmtree(bids_derivatives)

create_dirs(cases,bids_derivatives)



# ============================================================================================================
# workflow for obtaining inputs
pipe_inputs= Node(IdentityInterface(fields=['subject_id', 't2MaskCsv', 'outDir', 'force']), name='pipe_inputs')
pipe_inputs.set_input('outDir', bids_derivatives)
pipe_inputs.set_input('t1MaskCsv','t1')
pipe_inputs.set_input('t2MaskCsv','t2')
pipe_inputs.set_input('bse_dim','3')
pipe_inputs.iterables=[('subject_id', cases)]


templates = {'t1w': 'sub-{subject}/anat/*_T1w.nii.gz',
             't2w': 'sub-{subject}/anat/*_T2w.nii.gz',
             'dwi': 'sub-{subject}/dwi/*_dwi.nii.gz',
             'bvalFile': 'sub-{subject}/dwi/*_dwi.bval',
             'bvecFile': 'sub-{subject}/dwi/*_dwi.bvec'}

select_files= Node(SelectFiles(templates, base_directory= bids_data_dir), name= 'select_files')

inter_outputs= Node(Function(input_names=['id','dir'],
                             output_names= ['t1_align_prefix', 't2_align_prefix', 'dwi_align_prefix',
                             't1_mabsmask_prefix','t2_mabsmask_prefix', 'eddy_bse_betmask_prefix',
                             'fs_dir', 'fs_in_eddy', 'fs_in_epi',
                             'eddy_bse_prefix', 'eddy_bse_masked_prefix', 'eddy_epi_bse_prefix', 'eddy_epi_bse_masked_prefix',
                             'eddy_prefix', 'eddy_epi_prefix',
                             'eddy_tract_prefix','eddy_epi_tract_prefix',
                             'eddy_fs2dwi_dir', 'epi_fs2dwi_dir',
                             'eddy_wmql_dir', 'eddy_wmqlqc_dir', 'epi_wmql_dir', 'epi_wmqlqc_dir'],
                             function= define_outputs_wf), name='inter_outputs')




# ============================================================================================================
# structural pipeline
strct_pipeline= Workflow(name='strct_pipeline', base_dir= pipe_out_dir)
t1_align_node= Node(Align(), name='t1_align')
t2_align_node= Node(Align(), name='t2_align')
t1_mabsmask_node= Node(TrainingMask(), name='t1_mabs_mask')
t2_mabsmask_node= Node(TrainingMask(), name='t2_mabs_mask')
fs_node= Node(FsSeg(), name='freesurfer_seg')

strct_pipeline.connect([(pipe_inputs, select_files, [('subject_id', 'subject')]),
                       (select_files, t1_align_node, [('t1w', 'in_img')]),
                       (select_files, t2_align_node, [('t2w', 'in_img')]),
                       (pipe_inputs, t1_mabsmask_node, [('t1MaskCsv','csvFile')]),
                       (pipe_inputs, t2_mabsmask_node, [('t2MaskCsv','csvFile')]),
                       (pipe_inputs, inter_outputs, [('subject_id', 'id'), ('outDir','dir')]),
                       (inter_outputs, t1_align_node, [('t1_align_prefix','out_prefix')]),
                       (t1_align_node, t1_mabsmask_node, [('out_img','in_img')]),
                       (inter_outputs, t1_mabsmask_node, [('t1_mabsmask_prefix','out_prefix')]),
                       (inter_outputs, t2_align_node, [('t2_align_prefix','out_prefix')]),
                       (t2_align_node, t2_mabsmask_node, [('out_img','in_img')]),
                       (inter_outputs, t2_mabsmask_node, [('t2_mabsmask_prefix','out_prefix')]),
                       (inter_outputs, fs_node, [('fs_dir','fs_dir')]),
                       (t1_align_node, fs_node, [('out_img','t1_img')]),
                       (t1_mabsmask_node, fs_node, [('out_mask','t1_mask')]),
                       ])

strct_pipeline.write_graph('strct_pipeline.dot', graph2use='flat')
# strct_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
# strct_pipeline.run(updatehash=True)
# strct_pipeline.run()


# ============================================================================================================
# eddy pipeline
eddy_pipeline= Workflow(name='eddy_pipeline', base_dir= pipe_out_dir)
dwi_align_node= Node(Align(), name='axis_align_center')
eddy_node= Node(Eddy(), name='eddy_correct')
eddy_bse_node= Node(Bse(), name='baseline_img')
masking_node= Node(Masking(), name='multiply_by_mask')
dwi_bet_mask_node= Node(BetMask(), name='dwi_bet_mask')
eddy_ukf_node= Node(Ukf(), name='UKFTractography')
eddy_pipeline.connect([(strct_pipeline, dwi_align_node, [('inter_outputs.dwi_align_prefix','out_prefix')]),
                       (strct_pipeline, eddy_node, [('inter_outputs.eddy_prefix','out_prefix')]),
                       (select_files, dwi_align_node,[('dwi','in_img'), ('bvalFile','in_bval'), ('bvecFile','in_bvec')]),
                       (dwi_align_node, eddy_node, [('out_img', 'in_img'), ('out_bval', 'in_bval'), ('out_bvec', 'in_bvec')]),
                       (eddy_node, eddy_bse_node, [('out_img', 'in_img'), ('out_bval', 'in_bval')]),
                       (strct_pipeline, eddy_bse_node, [('inter_outputs.eddy_bse_prefix','bse_img')]),
                       (eddy_bse_node, dwi_bet_mask_node, [('out_img','in_img')]),
                       (strct_pipeline, dwi_bet_mask_node, [('inter_outputs.eddy_bse_betmask_prefix','out_prefix')]),
                       (strct_pipeline, masking_node, [('inter_outputs.eddy_bse_masked_prefix','out_prefix')]),
                       (eddy_bse_node, masking_node, [('out_img','in_img')]),
                       (pipe_inputs, masking_node, [('bse_dim','dim')]),
                       (dwi_bet_mask_node, masking_node, [('out_img','in_mask')]),
                       (dwi_bet_mask_node, eddy_ukf_node, [('out_img','in_mask')]),
                       (eddy_node, eddy_ukf_node, [('out_img','in_img')]),
                       (strct_pipeline, eddy_ukf_node, [('inter_outputs.eddy_tract_prefix','tract_file')]),
                       (eddy_node, eddy_ukf_node, [('out_bval','in_bval'), ('out_bvec','in_bvec')]),
                       ])


eddy_pipeline.write_graph('eddy_pipeline.dot', graph2use='flat')
# eddy_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
# eddy_pipeline.run(updatehash=True)
# eddy_pipeline.run()


# ============================================================================================================
# epi pipeline
epi_pipeline= Workflow(name='epi_pipeline', base_dir= pipe_out_dir)
epi_bse_node= Node(Bse(), name='baseline_img')
epi_node= Node(Epi(), name='epi_correct')
epi_ukf_node= Node(Ukf(), name='UKFTractography')
epi_pipeline.connect([(eddy_pipeline, epi_node, [('eddy_correct.out_img','dwi_img'),
                                                 ('eddy_correct.out_bval','in_bval'),
                                                 ('eddy_correct.out_bvec','in_bvec'),
                                                 ('multiply_by_mask.out_img','bse_img'),
                                                 ('dwi_bet_mask.out_img','dwi_mask')]),
                      (strct_pipeline, epi_node, [('inter_outputs.eddy_epi_prefix','out_prefix'), 
                                                  ('t2_align.out_img','t2_img'),
                                                  ('t2_mabs_mask.out_mask','t2_mask')]),
                      # (epi_node, epi_bse_node, [('out_img','in_img')]),
                      # (strct_pipeline, epi_bse_node, [('inter_outputs.eddy_epi_bse_prefix','bse_img')]),
                      (epi_node, epi_ukf_node, [('out_img','in_img'),('out_mask','in_mask')]),
                      (strct_pipeline, epi_ukf_node, [('inter_outputs.eddy_epi_tract_prefix','tract_file')]),
                      (epi_node, epi_ukf_node, [('out_bval','in_bval'), ('out_bvec','in_bvec')]),
                      ])


epi_pipeline.write_graph('epi_pipeline.dot', graph2use='flat')
# epi_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
# epi_pipeline.run(updatehash=True)
# epi_pipeline.run()

# ============================================================================================================
# fs2dwi registration pipeline
fs2dwi_pipeline= Workflow(name='fs2dwi_pipeline', base_dir= pipe_out_dir)
eddy_fs2dwi_node= Node(Fs2Dwi(),name='eddy_fs2dwi')
epi_fs2dwi_node= Node(Fs2Dwi(),name='epi_fs2dwi')
eddy_wmql_node= Node(Wmql(),name='eddy_wmql')
epi_wmql_node= Node(Wmql(),name='epi_wmql')
eddy_wmqlqc_node= Node(WmqlQc(),name='eddy_wmqlqc')
epi_wmqlqc_node= Node(WmqlQc(),name='epi_wmqlqc')
fs2dwi_pipeline.connect([(eddy_pipeline, eddy_fs2dwi_node, [('multiply_by_mask.out_img','bse')]),
                (strct_pipeline, eddy_fs2dwi_node, [('inter_outputs.eddy_fs2dwi_dir','out_dir'), ('inter_outputs.fs_dir','fs_dir')]),
                (epi_pipeline, epi_fs2dwi_node, [('epi_correct.out_bse','bse')]),
                (strct_pipeline, epi_fs2dwi_node, [('inter_outputs.epi_fs2dwi_dir','out_dir'), ('inter_outputs.fs_dir','fs_dir')]),
                (eddy_pipeline, eddy_wmql_node, [('UKFTractography.out_tract','tract_file')]),
                (epi_pipeline, epi_wmql_node, [('UKFTractography.out_tract','tract_file')]),
                (strct_pipeline, eddy_wmql_node, [('inter_outputs.fs_in_eddy','wmparc'), ('inter_outputs.eddy_wmql_dir','out_dir')]),
                (strct_pipeline, epi_wmql_node, [('inter_outputs.fs_in_epi','wmparc'), ('inter_outputs.epi_wmql_dir','out_dir')]),
                (eddy_wmql_node, eddy_wmqlqc_node, [('wmql_dir','wmql_dir')]),
                (epi_wmql_node, epi_wmqlqc_node, [('wmql_dir','wmql_dir')]),
                (strct_pipeline, eddy_wmqlqc_node, [('inter_outputs.eddy_wmqlqc_dir','out_dir')]),
                (strct_pipeline, epi_wmqlqc_node, [('inter_outputs.epi_wmqlqc_dir','out_dir')]),
                (pipe_inputs, eddy_wmqlqc_node, [('subject_id','subject_id')]),
                (pipe_inputs, epi_wmqlqc_node, [('subject_id','subject_id')]),
                ])


fs2dwi_pipeline.write_graph('fs2dwi_pipeline.dot', graph2use='flat')
# fs2dwi_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
# fs2dwi_pipeline.run(updatehash=True)
fs2dwi_pipeline.run()


