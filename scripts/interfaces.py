from nipype.interfaces.base import CommandLine, CommandLineInputSpec, File, TraitedSpec, traits, Directory

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
    in_img = File(exists=True, mandatory=True, argstr='csv -t %s')
    out_prefix = traits.String(mandatory=False, argstr='-o %s')
    csvFile = File(exists=True, mandatory=True, argstr='%s', position=-1)

class TrainingMaskOutputSpec(TraitedSpec):
    out_mask = File(desc='output image')


class TrainingMask(CommandLine):
    _cmd = 'atlas.py'
    input_spec = TrainingMaskInputSpec
    output_spec = TrainingMaskOutputSpec

    def _list_outputs(self):
        return {'out_mask': self.inputs.out_prefix+'-mask.nii.gz'}

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
        return {'out_img': self.inputs.bse_img + '.nii.gz'}

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

class Epi(CommandLine):
    _cmd = 'pnl_epi.py'
    input_spec = EpiInputSpec
    output_spec = EpiOutputSpec

    def _list_outputs(self):
        return {'out_img': self.inputs.out_prefix+'.nii.gz',
                'out_bval': self.inputs.out_prefix+'.bval',
                'out_bvec': self.inputs.out_prefix+'.bvec',
                'out_mask': self.inputs.out_prefix+'-mask.nii.gz'}

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
        return {'out_tract': self.inputs.tract_file + '.vtk'}


class WmqlInputSpec(CommandLineInputSpec):
    fs_dir = Directory(exists=True, mandatory=True, argstr='-f %s')
    tract_file = File(exists=True, mandatory=True, argstr='-i %s')
    out_dir = Directory(exists=False, mandatory=True, argstr='-o %s')


class WmqlOutputSpec(TraitedSpec):
    wmql_dir = File(desc='wmql dir')


class Wmql(CommandLine):
    _cmd = 'wmql.py'
    input_spec = WmqlInputSpec
    output_spec = WmqlOutputSpec

    def _list_outputs(self):
        return {'wmql_dir': self.inputs.out_dir}


