#!/usr/bin/env python

import vtk
import sys
import numpy
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

infile=sys.argv[1]
outfile=sys.argv[2]

# Read vtk
pdr = vtk.vtkPolyDataReader()
pdr.SetFileName(infile)
pdr.Update()
out = pdr.GetOutput()
pd = out.GetPointData()

# Get first tensor
tensors=pd.GetArray('tensor1')
if not tensors:
    tensors=pd.GetTensors()

# Replace nan's/inf's and set tensor attribute
if tensors is not None:
    tensors_np = vtk_to_numpy(tensors)
    tensors_np=numpy.nan_to_num(tensors_np) # replace nan's and inf's
    tensors=numpy_to_vtk(tensors_np)
    pd.SetTensors(tensors) #  set TENSOR array

# Write vtk
pdw = vtk.vtkPolyDataWriter()
#pdw.SetFileTypeToASCII()
pdw.SetFileTypeToBinary()
pdw.SetFileName(outfile)
pdw.SetTensorsName('tensor1')
#pdw.SetInput(out)
pdw.SetInputData(out)
pdw.Write()
pdw.Update()
