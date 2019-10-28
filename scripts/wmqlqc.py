#!/usr/bin/env python
from __future__ import print_function

from plumbum import local, cli, FG
import itertools
from os import getenv
from os.path import join as pjoin, isfile

def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]

class App(cli.Application):
    """Make html page of rendered wmql tracts. """

    wmqldirs = cli.SwitchAttr(
        ['-i'],
        help='list of wmql directories, must be enclosed within quotes',
        mandatory=True)

    caseids = cli.SwitchAttr(
        ['-s'],
        help='list of subject ids corrsponding to wmql directories, must be enclosed within quotes',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o'],
        cli.NonexistentPath,
        help='Output directory',
        mandatory=True)

    def main(self):

        PY2BIN= getenv('PY2BIN', None)
        if not PY2BIN:
            raise EnvironmentError('whitematteranalysis requires Python 2 interpreter, define export PY2BIN=/absolute/path/to/miniconda2/bin')

        else:
            wmqlqc_tract_path = pjoin(PY2BIN, 'wm_quality_control_tractography.py')
            if isfile(wmqlqc_tract_path):
                wm_quality_control_tractography = local[wmqlqc_tract_path]
            else:
                raise FileNotFoundError(f'whitematteranalysis not found in {PY2BIN}, see README.md for instruction')

        tuples = zip(self.caseids.split(), map(local.path, self.wmqldirs.split()))
        vtks = [(caseid, vtk) for (caseid, d) in tuples for vtk in d // '*.vtk']
        keyfn = lambda x : local.path(x).name[:-4]
        groupedvtks = itertools.groupby(sorted(vtks, key=keyfn), key=keyfn)
        self.out.mkdir()
        for group, vtks in groupedvtks:
            vtkdir = self.out / group
            qcdir = self.out / (group + '-qc')
            print("Make symlinks for vtk group {}".format(group))
            vtkdir.mkdir()
            for (caseid, vtk) in vtks:
                symlink = vtkdir / (vtk.name[:-4] + '_' + caseid + '.vtk')
                print("Make symlink for caseid '{}': {}".format(caseid, symlink))
                vtk.symlink(symlink)
            print("Render tracts for vtk group {}".format(group))
            wm_quality_control_tractography[vtkdir, qcdir] & FG

if __name__ == '__main__':
    App.run()
