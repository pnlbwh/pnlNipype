from nipype.interfaces.base import CommandLine, CommandLineInputSpec, File, TraitedSpec, traits, Directory
from os.path import join as pjoin

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
class TrainingMaskInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-t %s')
    out_prefix = traits.String(mandatory=True, argstr='-o %s')
    csvFile = traits.String(mandatory=True, argstr='--train %s')

class TrainingMaskOutputSpec(TraitedSpec):
    out_mask = File(desc='output image')


class TrainingMask(CommandLine):
    _cmd = 'atlas.py'
    input_spec = TrainingMaskInputSpec
    output_spec = TrainingMaskOutputSpec

    def _list_outputs(self):
        return {'out_mask': self.inputs.out_prefix+'_mask.nii.gz'}

# ============================================================================================================
class BetMaskInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')


class BetMaskOutputSpec(TraitedSpec):
    out_img = File(desc='output image')


class BetMask(CommandLine):
    _cmd = 'bet_mask.py'
    input_spec = BetMaskInputSpec
    output_spec = BetMaskOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'_mask.nii.gz'}


# ============================================================================================================
class MaskingInputSpec(CommandLineInputSpec):
    in_img = traits.String(exists=True, mandatory=True, argstr='-i %s')
    in_mask = File(exists=True, mandatory=True, argstr='-m %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s.nii.gz')
    dim = traits.String(mandatory=True, argstr='-d %s')


class MaskingOutputSpec(TraitedSpec):
    out_img = File(desc='output image')


class Masking(CommandLine):
    _cmd = 'masking.py'
    input_spec = MaskingInputSpec
    output_spec = MaskingOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz'}




# ============================================================================================================
class BseInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    bse_img = traits.String(mandatory=False, argstr='-o %s.nii.gz')


class BseOutputSpec(TraitedSpec):
    out_img = File(desc='output image')


class Bse(CommandLine):
    _cmd = 'bse.py'
    input_spec = BseInputSpec
    output_spec = BseOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.bse_img+'.nii.gz'}


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
    dwi_img = File(exists=True, mandatory=True, argstr='--dwi %s ')
    dwi_mask = File(exists=True, mandatory=True, argstr='--dwimask %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')
    t2_img = File(exists=True, mandatory=True, argstr='--t2 %s')
    t2_mask = File(exists=True, mandatory=True, argstr='--t2mask %s')
    bse_img = File(exists=True, mandatory=False, argstr='--bse %s')

class EpiOutputSpec(TraitedSpec):
    out_img = File(desc='output image')
    out_bval = File(desc='output bval')
    out_bvec = File(desc='output bvec')
    out_mask = File(desc='output mask')
    out_bse = File(desc='output bse')

class Epi(CommandLine):
    _cmd = 'pnl_epi.py'
    input_spec = EpiInputSpec
    output_spec = EpiOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz',
                'out_bval': self.inputs.out_prefix+'.bval',
                'out_bvec': self.inputs.out_prefix+'.bvec',
                'out_mask': self.inputs.out_prefix+'_mask.nii.gz',
                'out_bse': self.inputs.out_prefix+'_bse.nii.gz'}

# ============================================================================================================
class UkfInputSpec(CommandLineInputSpec):
    in_img = File(exists=True, mandatory=True, argstr='-i %s')
    in_bval = File(exists=True, mandatory=False, argstr='--bvals %s')
    in_bvec = File(exists=True, mandatory=False, argstr='--bvecs %s')
    in_mask = File(exists=True, mandatory=False, argstr='-m %s')
    tract_file = traits.String(mandatory=False, argstr='-o %s.vtk')


class UkfOutputSpec(TraitedSpec):
    out_tract = File(desc='output image')


class Ukf(CommandLine):
    _cmd = 'ukf.py'
    input_spec = UkfInputSpec
    output_spec = UkfOutputSpec

    def _list_outputs(self):
        return {'out_tract': self.inputs.tract_file+'.vtk'}

# ============================================================================================================
class WmqlInputSpec(CommandLineInputSpec):
    wmparc = File(exists=True, mandatory=True, argstr='-f %s')
    tract_file = File(exists=True, mandatory=True, argstr='-i %s')
    out_dir = traits.String(exists=False, mandatory=True, argstr='-o %s')


class WmqlOutputSpec(TraitedSpec):
    wmql_dir = Directory(desc='wmql dir')


class Wmql(CommandLine):
    _cmd = 'wmql.py'
    input_spec = WmqlInputSpec
    output_spec = WmqlOutputSpec

    def _list_outputs(self):
        return {'wmql_dir': self.inputs.out_dir}



# ============================================================================================================
class WmqlQcInputSpec(CommandLineInputSpec):
    wmql_dir = Directory(exists=True, mandatory=True, argstr='-i %s')
    subject_id = traits.String(mandatory=True, argstr='-s %s')
    out_dir = traits.String(mandatory=True, argstr='-o %s')


class WmqlQcOutputSpec(TraitedSpec):
    wmqlqc_dir = Directory(desc='wmqlqc dir')


class WmqlQc(CommandLine):
    _cmd = 'wmqlqc.py'
    input_spec = WmqlQcInputSpec
    output_spec = WmqlQcOutputSpec

    def _list_outputs(self):
        return {'wmqlqc_dir': self.inputs.out_dir}




# ============================================================================================================
class Fs2DwiInputSpec(CommandLineInputSpec):
    fs_dir = Directory(exists=True, mandatory=True, argstr='-f %s')
    bse = File(exists=True, mandatory=False, argstr='--bse %s')
    dwi = File(exists=True, mandatory=False, argstr='--dwi %s')
    dwimask = File(exists=True, mandatory=False, argstr='--dwimask %s')    
    out_dir = traits.String(mandatory=True, position=-1, argstr='-o %s direct')


class Fs2DwiOutputSpec(TraitedSpec):
    wmparc = File(desc='wmparc')
        

class Fs2Dwi(CommandLine):
    _cmd = 'fs2dwi.py'
    input_spec = Fs2DwiInputSpec
    output_spec = Fs2DwiOutputSpec

    def _list_outputs(self):
        return {'wmparc': pjoin(self.inputs.out_dir,'wmparcInDwi.nii.gz')}



# ============================================================================================================
class FsSegInputSpec(CommandLineInputSpec):
    fs_dir = traits.String(exists=True, mandatory=True, argstr='-o %s')
    t1_img = File(exists=True, mandatory=True, argstr='-i %s')
    t1_mask = File(exists=True, mandatory=True, argstr='-m %s')

class FsSegOutputSpec(TraitedSpec):
    fs_dir = Directory(desc='freesurfer dir')


class FsSeg(CommandLine):
    # _cmd = 'fs.py'
    _cmd = 'cp -a /home/tb571/Downloads/pnlpipe/_data/003_GNX_007/FreeSurferUsingMask-003_GNX_007-b13e54312f/* /home/tb571/Downloads/INTRuST_BIDS/derivatives/pnlNipype/sub-003GNX007/anat/freesurfer #'
    input_spec = FsSegInputSpec
    output_spec = FsSegOutputSpec
    
    def _list_ouputs(self):
        return {'fs_dir': self.inputs.fs_dir}



# ============================================================================================================
def define_outputs_wf(id, dir):
    '''
    :param id: subject_id
    :param dir: /path/to/derivatives/ directory
    :param force: delete previous outputs
    :return: output of each script
    '''
    from os.path import join as pjoin

    t1_align_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-Xc_T1w')
    t2_align_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-Xc_T2w')
    dwi_align_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-Xc_dwi')

    t1_mabsmask_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-T1wXcMabs')
    t2_mabsmask_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-T2wXcMabs')
    
    fs_dir = pjoin(dir, f'sub-{id}', 'anat', 'freesurfer')

    eddy_bse_betmask_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcBseBet')

    eddy_bse_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEd_bse')
    eddy_bse_masked_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdMa_bse')
    eddy_epi_bse_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdEp_bse')
    eddy_epi_bse_masked_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdEpMa_bse')

    eddy_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcEd_dwi')
    eddy_epi_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcEdEp_dwi')
    
    eddy_fs2dwi_dir = pjoin(dir, f'sub-{id}', 'fs2dwi', 'eddy_fs2dwi')
    fs_in_eddy = pjoin(dir, f'sub-{id}', 'fs2dwi', 'eddy_fs2dwi', 'wmparcInDwi.nii.gz')
    # fs_in_eddy = pjoin(dir, f'sub-{id}', 'fs2dwi', 'eddy_fs2dwi', f'sub-{id}_space-dwi_desc-XcEd_wmparc.nii.gz')
    epi_fs2dwi_dir = pjoin(dir, f'sub-{id}', 'fs2dwi', 'epi_fs2dwi')
    fs_in_epi = pjoin(dir, f'sub-{id}', 'fs2dwi', 'epi_fs2dwi', 'wmparcInDwi.nii.gz')
    # fs_in_epi = pjoin(dir, f'sub-{id}', 'fs2dwi', 'epi_fs2dwi', f'sub-{id}_space-dwi_desc-XcEdEp_wmparc.nii.gz')

    eddy_tract_prefix = pjoin(dir, f'sub-{id}', 'tracts', f'sub-{id}_desc-XcEd')
    eddy_epi_tract_prefix = pjoin(dir, f'sub-{id}', 'tracts', f'sub-{id}_desc-XcEdEp')

    eddy_wmql_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmql', 'eddy')
    eddy_wmqlqc_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc', 'eddy')
    epi_wmql_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmql', 'epi')
    epi_wmqlqc_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc', 'epi')
    

    return (t1_align_prefix, t2_align_prefix, dwi_align_prefix,
            t1_mabsmask_prefix, t2_mabsmask_prefix, eddy_bse_betmask_prefix,
            fs_dir, fs_in_eddy, fs_in_epi,
            eddy_bse_prefix, eddy_bse_masked_prefix, eddy_epi_bse_prefix, eddy_epi_bse_masked_prefix,
            eddy_prefix, eddy_epi_prefix, 
            eddy_tract_prefix, eddy_epi_tract_prefix,
            eddy_fs2dwi_dir, epi_fs2dwi_dir,
            eddy_wmql_dir, eddy_wmqlqc_dir, epi_wmql_dir, epi_wmqlqc_dir)


def create_dirs(cases, dir):
    from shutil import rmtree
    from os import makedirs
    from os.path import isdir
    from os.path import join as pjoin
    
    if not isdir(dir): 
        for id in cases:
            makedirs(pjoin(dir, f'sub-{id}', 'anat'))
            makedirs(pjoin(dir, f'sub-{id}', 'dwi'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts'))
            makedirs(pjoin(dir, f'sub-{id}', 'anat', 'freesurfer'))
            makedirs(pjoin(dir, f'sub-{id}', 'fs2dwi'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmql'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc'))

