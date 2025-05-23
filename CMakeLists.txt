set(proj pnlNipype)

set(${proj}_DEPENDENCIES "")

set(_install_deps COMMAND ${CMAKE_COMMAND}
    ${PYTHON_EXECUTABLE} -m pip install git+https://github.com/pnlbwh/conversion.git
    )

