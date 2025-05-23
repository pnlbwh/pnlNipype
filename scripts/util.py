__version__ = '0.1.3'

from os.path import abspath, dirname, join as pjoin, isfile
import os
from plumbum import local
from tempfile import TemporaryDirectory

FILEDIR= abspath(dirname(__file__))
LIBDIR= dirname(FILEDIR)
ROOTDIR= dirname(LIBDIR)

# sys.path.append(FILEDIR)
# sys.path.append(LIBDIR)

BET_THRESHOLD = '0.25'
B0_THRESHOLD = 50
N_PROC = '4'
REPOL_BSHELL_GREATER= 550
QC_POLL= 30 # seconds


TMPDIR= local.path(os.getenv('PNLPIPE_TMPDIR',pjoin(os.environ['HOME'],'tmp')))
if not TMPDIR.exists():
    TMPDIR.mkdir()


from nibabel import load as load_nifti, Nifti1Image


def save_nifti(fname, data, affine, hdr=None):
    if data.dtype.name=='uint8':
        hdr.set_data_dtype('uint8')
    elif data.dtype.name=='int16':
        hdr.set_data_dtype('int16')
    else:
        hdr.set_data_dtype('float32')

    result_img = Nifti1Image(data, affine, header=hdr)
    result_img.to_filename(fname)


def logfmt(scriptname):
    return '%(asctime)s ' + scriptname + ' %(levelname)s  %(message)s'

from multiprocessing import cpu_count
N_CPU= cpu_count()

