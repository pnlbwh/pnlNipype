set(proj pnlNipype)

set(${proj}_DEPENDENCIES "")

include(ExternalProject)

set(_install_deps COMMAND ${CMAKE_COMMAND}
    ${PYTHON_EXECUTABLE} -m pip install git+https://github.com/pnlbwh/conversion.git
    )

ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/scripts
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ${CMAKE_COMMAND} -E  echo_append ""
    ${_install_deps}
    DEPENDS
        ${${proj}_DEPENDENCIES}
    )

ExternalProject_GenerateProjectDescription_Step(${proj})

mark_as_superbuild(
    LABELS "PYTHONPATH_LAUNCHER_BUILD"
    )

ExternalProject_Get_Property(${proj} STAMP_DIR)
