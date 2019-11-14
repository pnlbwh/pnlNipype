#!/usr/bin/env python

from nipype import Node, Function, Workflow, SelectFiles
from nipype.interfaces import DataSink
from nipype.interfaces.base import CommandLine, CommandLineInputSpec, File, TraitedSpec, traits, Directory
from conversion import read_cases
from os.path import join as pjoin, basename, isdir
from os import makedirs
from shutil import rmtree

# ============================================================================================================
parent_directory= '/tmp/dwi_pipeline/'

output_base_dir= pjoin(parent_directory, 'derivatives/tmp')
if isdir(output_base_dir):
    rmtree(output_base_dir)
makedirs(output_base_dir)

input_base_directory= '/home/tb571/Downloads/INTRuST_BIDS/'
cases= read_cases(pjoin(input_base_directory, 'caselist.txt'))


# ============================================================================================================
class AlignInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')


class AlignOutputSpec(TraitedSpec):
    out_img = File(desc='output image')
    out_bval = File(desc='output bval')
    out_bvec = File(desc='output bvec')


class Align(CommandLine):
    _cmd = 'align.py'
    input_spec = AlignInputSpec
    output_spec = AlignOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz',
                'out_bval': self.inputs.out_prefix+'.bval',
                'out_bvec': self.inputs.out_prefix+'.bvec'}



# ============================================================================================================
class EddyInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')


class EddyOutputSpec(TraitedSpec):
    out_img = File(desc='output image')
    out_bval = File(desc='output bval')
    out_bvec = File(desc='output bvec')


class Eddy(CommandLine):
    _cmd = 'pnl_eddy.py'
    input_spec = EddyInputSpec
    output_spec = EddyOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz',
                'out_bval': self.inputs.out_prefix+'.bval',
                'out_bvec': self.inputs.out_prefix+'.bvec'}


# ============================================================================================================
class EpiInputSpec(CommandLineInputSpec):
    dwi_img = File(exists=True, mandatory=True, argstr='--dwi %s')
    dwi_mask = File(exists=True, mandatory=True, argsr='--dwimask %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')
    t2_img = File(exists=True, mandatory=True, argstr='--t2 %s')
    t2_mask = File(exists=True, mandatory=True, argstr='--t2mask %s')

class EpiOutputSpec(TraitedSpec):
    out_img = File(desc='output image')
    out_bval = File(desc='output bval')
    out_bvec = File(desc='output bvec')
    out_mask = File(desc='output mask')

class Epi(CommandLine):
    _cmd = 'pnl_epi.py'
    input_spec = EpiInputSpec
    output_spec = EpiOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz',
                'out_bval': self.inputs.out_prefix+'.bval',
                'out_bvec': self.inputs.out_prefix+'.bvec',
                'out_mask': self.inputs.out_prefix+'_mask.nii.gz'}


# ============================================================================================================
class BseInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    bse_img = traits.String(mandatory=False, argstr='-o %s')


class BseOutputSpec(TraitedSpec):
    out_img = File(desc='output image')
    

class Bse(CommandLine):
    _cmd = 'bse.py'
    input_spec = BseInputSpec
    output_spec = BseOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.bse_img}



# ============================================================================================================
class MaskInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')


class MaskOutputSpec(TraitedSpec):
    out_img = File(desc='output image')


class Mask(CommandLine):
    _cmd = 'bet_mask.py'
    input_spec = MaskInputSpec
    output_spec = MaskOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'_mask.nii.gz'}


# ============================================================================================================
class UkfInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    in_mask = File(exists=True, mandatory=False, argstr='-m %s')
    tract_file = traits.String(mandatory=False, argstr='-o %s')
    

class UkfOutputSpec(TraitedSpec):
    out_tract = File(desc='output image')


class Ukf(CommandLine):
    _cmd = 'ukf.py'
    input_spec = UkfInputSpec
    output_spec = UkfOutputSpec

    def _list_outputs(self):
        return {'out_tract': self.inputs.tract_file}


class WmqlInputSpec(CommandLineInputSpec):
    fs_dir = Directory(exists=True, mandatory=True, argstr='-f %s')
    tract_file = File(exists=True, mandatory=True, argstr='-i %s')
    out_dir = Directory(exists=False, mandatory= True, argstr='-o %s')
    

class WmqlOutputSpec(TraitedSpec):
    wmql_dir = File(desc='wmql dir')


class Wmql(CommandLine):
    _cmd = 'wmql.py'
    input_spec = WmqlInputSpec
    output_spec = WmqlOutputSpec

    def _list_outputs(self):
        return {'wmql_dir': self.inputs.out_dir}


# ============================================================================================================
def intermediate_outputs_wf(input_file_name):
    from os.path import join as pjoin, basename

    prefix = basename(input_file_name).split('.')[0]
    parent_directory = '/tmp/dwi_pipeline/'
    output_base_dir = pjoin(parent_directory, 'derivatives/tmp')
    outPrefix = pjoin(output_base_dir, prefix)

    align_prefix = outPrefix + '-xc'
    eddy_prefix = outPrefix + '-eddy'
    epi_prefix = outPrefix + '-epi'
    bse_output = outPrefix + '-bse.nii.gz'
    bet_prefix = outPrefix
    ukf_output = outPrefix + '.vtk'

    return (align_prefix, eddy_prefix, epi_prefix, bse_output, bet_prefix, ukf_output)

def_inter_node= Node(Function(input_names=['input_file_name'],
                output_names= ['align_prefix', 'eddy_prefix', 'epi_prefix', 'bse_output', 'bet_prefix', 'ukf_output'],
                function= intermediate_outputs_wf), name='def_inter_outputs')




# ============================================================================================================
templates = {'t1w': 'sub-{subject}/anat/*T1w.nii.gz',
              't2w': 'sub-{subject}/anat/*T2w.nii.gz',
              'dwi': 'sub-{subject}/dwi/*dwi.nii.gz',
              'bvalFile': 'sub-{subject}/dwi/*dwi.bval',
              'bvecFile': 'sub-{subject}/dwi/*dwi.bvec'}

select_files= Node(SelectFiles(templates, base_directory= input_base_directory), name= 'select_files')
# select_files.iterables = [('subject', ['003_GNX_007'])] 
select_files.iterables = [('subject', cases)]



# ============================================================================================================
data_sink = Node(DataSink(base_directory=pjoin(parent_directory, 'derivatives')), name='datasink')



# ============================================================================================================
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
                       (eddy_node, data_sink, [('out_img', 'eddy_corrected'), ('out_bval', 'eddy_corrected.@bval'), ('out_bvec', 'eddy_corrected.@bvec')]),
                       (eddy_node, bse_node, [('out_img', 'in_img'), ('out_bval', 'in_bval')]),
                       (def_inter_node, bse_node, [('bse_output','bse_img')]),  
                       (bse_node, mask_node, [('out_img','in_img')]),
                       (def_inter_node, mask_node, [('bet_prefix','out_prefix')]),
                       (mask_node, ukf_node, [('out_img','in_mask')]),
                       (eddy_node, ukf_node, [('out_img','in_img')]),
                       (def_inter_node, ukf_node, [('ukf_output','tract_file')]),
                       (eddy_node, ukf_node, [('out_bval','in_bval'), ('out_bvec','in_bvec')]),
                       (ukf_node, data_sink, [('out_tract', 'tracts')])
                       ])


eddy_pipeline.write_graph('eddy_pipeline.dot', graph2use='flat')

eddy_pipeline.run('MultiProc', plugin_args={'n_procs': 3})
# eddy_pipeline.run()

