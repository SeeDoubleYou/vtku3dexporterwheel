import subprocess
import os
import sys
import vtk

from build_u3d import clone_u3d


is_win = (sys.platform == 'win32')
is_darwin = (sys.platform == 'darwin')


def download_install_ninja_win(version="1.8.2", zip_file="src/ninja.zip"):
    os.makedirs(os.path.dirname(zip_file), exist_ok=True)
    if not os.path.isfile(zip_file):
        print(f"> downloading ninja v{version}")
        from urllib.request import urlretrieve
        url = f"https://github.com/ninja-build/ninja/releases/download/v{version}/ninja-win.zip"
        urlretrieve(url, zip_file)

    current = subprocess.check_output("ninja --version", shell=True).decode().strip()
    if version != current:
        print(f"> overwriting ninja (v{current}) with v{version}")
        scripts_dir = os.path.join(sys.prefix, "Scripts")
        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zh:
            zh.extractall(scripts_dir)

        current = subprocess.check_output("ninja --version", shell=True).decode().strip()
        if version != current:
            exit(f"> overwriting ninja FAILED")
        print(f"> overwriting ninja succeeded")


def generate_libpython(filepath="work/vtk/libpython.notreally"):
    """
    According to PEP513 you are not allowed to link against libpythonxxx.so. However, CMake demands it. So here you go.
    An empty libpythonxxx.so.
    """
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, mode='w') as fh:
            fh.write('')
    return filepath


def build_vtku3dexporter(src="../../src/u3d/Samples/SampleCode",
                         work="work/vtku3dexporter",
                         build="../../build_vtku3dexporter",
                        #  python_library="/usr/local/Cellar/python3/3.6.4_2/Frameworks/Python.framework/Versions/3.6/lib/libpython3.6m.dylib",
                        #  generator="Ninja",
                        #  install_cmd="ninja -j 1 install",
                         generator="Unix Makefiles",
                         install_cmd="make install",
                         install_dev=True,
                         clean_cmake_cache=True):
    """Build and install VTKU3DExporter using CMake."""
    build_cmd = []
    if is_win:
        python_include_dir = f"{sys.prefix}/include"
        # only support VS2017 build tools for now
        vcvarsall_cmd = "\"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\BuildTools\\VC\\Auxiliary\\Build\\vcvarsall.bat\" amd64"  # noqa
        build_cmd.append(vcvarsall_cmd)
    elif is_darwin:
        version_string = f"{sys.version_info[0]}.{sys.version_info[1]}{sys.abiflags}"
        python_include_dir = f"{sys.prefix}/include/python{version_string}"
    else:
        version_string = f"{sys.version_info[0]}.{sys.version_info[1]}{sys.abiflags}"
        python_include_dir = f"{sys.prefix}/include/python{version_string}"

    # being helpful
    validation_errors = []
    # if not os.path.exists(python_library):
    #     validation_errors.append(f"!! python_library does not exist at: '{python_library}'")
    if not os.path.exists(python_include_dir):
        validation_errors.append(f"!! python_include_dir does not exist at: '{python_include_dir}'")
    if validation_errors:
        raise ValueError("\n".join(validation_errors))

    # Help Cmake find the u3d lib
    u3d_build_path = os.path.abspath('build_u3d')
    print(os.path.abspath(os.path.curdir))
    vtk_dir_path = os.path.normpath(os.path.join(sys.prefix, 'lib/python3.6/site-packages/vtk'))
    print(vtk_dir_path)
    vtk_notreally_path = os.path.abspath('work/vtk')
    print(vtk_notreally_path)
    # print(os.path.abspath(os.path.curdir))

    # compose cmake command
    cmake_cmd = ["cmake"]
    if clean_cmake_cache and os.path.exists(work):
        cmake_cmd.append("-U *")
    cmake_cmd.extend([
        src,
        f"-G \"{generator}\"",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX:PATH={build}",
        # f"-DCMAKE_LIBRARY_PATH:PATH=\"{vtk_notreally_path}\"",
        # f"-DPATHS={u3d_build_path}:{vtk_notreally_path}",
        f"-DCMAKE_PREFIX_PATH:PATH=\"{u3d_build_path}\"",
        f"-DVTK_DIR={vtk_dir_path}",
        # PythonLibs options https://cmake.org/cmake/help/latest/module/FindPythonLibs.html
        f"-DPYTHON_INCLUDE_DIR:PATH=\"{python_include_dir}\"",
        # f"-DPYTHON_LIBRARY:FILEPATH=\"{python_library}\"",
        # PythonInterp options https://cmake.org/cmake/help/latest/module/FindPythonInterp.html
        f"-DPYTHON_EXECUTABLE:FILEPATH=\"{sys.executable}\"",
        # Wrapping options
        "-DWRAP_PYTHON:BOOL=ON",
        f"-DINSTALL_PYTHON_MODULE_DIR:PATH=\".\"",
    ])
    # rpath settings
    # https://github.com/jcfr/VTKPythonPackage/blob/b30ce84696a3ea0bcf42052646a28bdf854ac819/CMakeLists.txt#L175
    # https://cmake.org/Wiki/CMake_RPATH_handling
    if is_darwin:
        cmake_cmd.extend([
            "-DCMAKE_INSTALL_NAME_DIR:STRING=@loader_path",
            "-DCMAKE_INSTALL_RPATH:STRING=@loader_path",
            "-DCMAKE_OSX_DEPLOYMENT_TARGET='10.13'",
        ])
    elif not is_win:
        cmake_cmd.extend([
            "-DCMAKE_INSTALL_RPATH:STRING=\$ORIGIN",
        ])

    build_cmd.append(" ".join(cmake_cmd))
    build_cmd.append(install_cmd)

    build_cmd = " && ".join(build_cmd)
    print(f"> configuring, building and installing VTKU3DExporter")
    print(f"> {build_cmd}")

    os.makedirs(work, exist_ok=True)
    subprocess.check_call(build_cmd, shell=True, cwd=work)


if __name__ == "__main__":
    if is_win:
        # could not get it to work with the version of ninja that is on pypi, so put it on the current path
        download_install_ninja_win()

    generate_libpython()
    clone_u3d(branch='export-mesh-names')
    build_vtku3dexporter()