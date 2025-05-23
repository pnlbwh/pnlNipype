cmake_minimum_required(VERSION 3.20)

project(pnlNipype)

set(proj pnlNipype)

set(${proj}_DEPENDENCIES "")

include(ExternalProject)

ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/scripts
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ""
    DEPENDS
        ${${proj}_DEPENDENCIES}
    )

ExternalProject_Get_Property(${proj} STAMP_DIR)
