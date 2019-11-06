#!/usr/bin/env python

from align import work_flow as align_wf
from pnl_eddy import work_flow as pnl_eddy_wf
from pnl_epi import work_flow as pnl_epi_wf
from bse import work_flow as bse_wf
from bet_mask import work_flow as bet_mask_wf
from ukf import work_flow as ukf_wf

from nipype import Node, Function, Workflow


align_node= Node(Function(input_names=['img_file', 'out_prefix', 'axisAlign', 'center', 'bval_file', 'bvec_file'],
                output_names=['alignedImg','alignedBval', 'alignedBvec']), function= align_wf, name= 'axis_align_center')

eddy_node= Node(Function(input_names=['dwi', 'bvalFile', 'bvecFile', 'out', 'debug', 'overwrite', 'nproc'],
                output_names=['ed_dwi', 'ed_bval', 'ed_bvec']), function= pnl_eddy_wf, name= 'eddy_correct')

epi_node= Node(Function(input_names=['dwi', 'bsein', 'dwimask', 't2', 't2mask', 'bvals_file', 'bvecs_file', 'out', 'debug', 'nproc', 'force'],
                output_names=['ep_dwi', 'ep_bval', 'ep_bvec', 'ep_mask']), function= pnl_epi_wf, name= 'epi_correct')

bse_node= Node(Function(input_names= ['dwi', 'bval_file', 'out', 'b0_threshold', 'dwimask', 'minimum', 'average', 'all'],
               output_names=['bse_img']), function= bse_wf, name= 'b0_extraction')

bet_node= Node(Function(input_names=['img', 'bval_file', 'out', 'bet_threshold'],
               output_names=['brain_mask']), function= bet_mask_wf, name= 'bet_masking')

ukf_node= Node(Function(input_names=['dwi', 'dwimask', 'bvalFile', 'bvecFile', 'out', 'givenParams'],
               output_names=['vtkFile']), function= ukf_wf, name= 'ukf_tracrography')

# needs definition
# datasource
# align_node: img_file, bval_file, bvec_file, out_prefix
# eddy_node: out
# epi_node: t2, t2mask, out
# bse_node: out
# bet_node: out
# ukf_node: out
# datasink


# ============================================================================================================
eddy_pipeline= Workflow(name='eddy_pipeline', base_dir= '/tmp/dwi_pipeline/eddy_correct')

eddy_pipeline.connect([(align_node, eddy_node, [('alignedImg', 'dwi'), ('alignedBval', 'bvalFile'), ('alignedBvec', 'bvecFile')]),
                       (eddy_node, bse_node, [('ed_dwi', 'dwi'), ('ed_bval', 'bval_file')]),
                       (bse_node, bet_node, [('bse_img', 'img')]),
                       (bet_node, ukf_node, [('brain_mask', 'dwimask')]),
                       (eddy_node, ukf_node, [('ed_dwi', 'dwi'), ('ed_bval','bvalFile'), ('ed_bvec', 'bvecFile')])
                       ])

eddy_pipeline.write_graph('eddy_pipeline.dot', graph2use='flat')




# ============================================================================================================
epi_pipeline= Workflow(name='epi_pipeline', base_dir= '/tmp/dwi_pipeline/epi_correct')

epi_pipeline.connect([(align_node, eddy_node, [('alignedImg', 'dwi'), ('alignedBval', 'bvalFile'), ('alignedBvec', 'bvecFile')]),
                      (eddy_node, bse_node, [('ed_dwi', 'dwi'), ('ed_bval', 'bval_file')]),
                      (eddy_node, epi_node, [('ed_bval', 'bvals_file'), ('ed_bvec','bvecs_file')]),
                      (bse_node, bet_node, [('bse_img', 'img')]),
                      (eddy_node, epi_node, [('ed_dwi', 'dwi')]),
                      (bse_node, epi_node, [('bse_img', 'bsein')]),
                      (bet_node, epi_node, [('brain_mask','dwimask')]),
                      (epi_node, ukf_node, [('ep_dwi', 'dwi'), ('ep_bval','bvalFile'), ('ep_bvec', 'bvecFile'), ('ep_mask', 'dwimask')])
                      ])


epi_pipeline.write_graph('epi_pipeline.dot', graph2use='flat')


