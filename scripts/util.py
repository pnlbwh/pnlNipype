__version__ = '0.1.3'

from os.path import abspath, dirname, join as pjoin, isfile
import os
from plumbum import local
from tempfile import mkdtemp
import weakref, shutil

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

TMPDIR= local.path(os.getenv('PNLPIPE_TMPDIR','/tmp/'))
# TMPDIR= local.path(os.getenv('PNLPIPE_TMPDIR',pjoin(os.environ['HOME'],'tmp'))
if not TMPDIR.exists():
    TMPDIR.mkdir()


import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
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

import psutil
N_CPU= psutil.cpu_count()


# the following context manager is copied from https://github.com/python/cpython/blob/master/Lib/tempfile.py#L762
class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:
        with TemporaryDirectory() as tmpdir:
            ...
    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix=None, prefix=None, dir=TMPDIR):
        self.name = mkdtemp(suffix, prefix, dir)
        self._finalizer = weakref.finalize(
            self, self._cleanup, self.name,
            warn_message="Implicitly cleaning up {!r}".format(self))

    @classmethod
    def _rmtree(cls, name):
        def onerror(func, path, exc_info):
            if issubclass(exc_info[0], PermissionError):
                def resetperms(path):
                    try:
                        os.chflags(path, 0)
                    except AttributeError:
                        pass
                    os.chmod(path, 0o700)

                try:
                    if path != name:
                        resetperms(os.path.dirname(path))
                    resetperms(path)

                    try:
                        os.unlink(path)
                    # PermissionError is raised on FreeBSD for directories
                    except (IsADirectoryError, PermissionError):
                        cls._rmtree(path)
                except FileNotFoundError:
                    pass
            elif issubclass(exc_info[0], FileNotFoundError):
                pass
            else:
                exit(1)

        shutil.rmtree(name, onerror=onerror)

    @classmethod
    def _cleanup(cls, name, warn_message):
        cls._rmtree(name)
        warnings.warn(warn_message, ResourceWarning)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        self.cleanup()

    def cleanup(self):
        if self._finalizer.detach():
            self._rmtree(self.name)

