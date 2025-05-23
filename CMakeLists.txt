cmake_minimum_required(VERSION 3.20)

project(pnlNipype)

set(proj pnlNipype)

set(${proj}_DEPENDENCIES "")

include(ExternalProject)

execute_process(COMMAND wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh)
execute_process(COMMAND bash Miniforge3-Linux-x86_64.sh -b -p ${CMAKE_BINARY_DIR}/miniconda3)

set(PYTHON_DIR ${CMAKE_BINARY_DIR}/miniconda3/bin)
execute_process(COMMAND ${PYTHON_DIR}/pip install git+https://github.com/pnlbwh/conversion.git)
execute_process(COMMAND sed -i "1s+/usr/bin/env python+${PYTHON_DIR}/python+g" ${CMAKE_SOURCE_DIR}/scripts/ukf.py)

ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/scripts
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ""
    DEPENDS
        ${${proj}_DEPENDENCIES}
    )

ExternalProject_Get_Property(${proj} STAMP_DIR)
