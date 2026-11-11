# Copyright ORNL

import platform
from pathlib import Path
from typing import Dict, List, Set

from spack.package import *
from spack.vendor import distro
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage
from spack_repo.nccs.build_systems.tarball import (
    TarballPackage,
    get_base_tarball_url,
    map_to_enterprise_distro,
)

_BLANK_FILE_URL: str = f"file://{Path(__file__).resolve().parent.joinpath('BLANK')}"
_BLANK_FILE_HASH: str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

_TOOLCHAINS: List[str] = ["amd", "cray", "gnu", "intel"]

_VERSION_HASH_MAP: Dict = {
    "9.2.0": {
        "rhel-x86_64-cray": "e8ae9bd80822b84836ee8057641ced150fcdf475b60db4868ea83a8f0eba9c1f",
        "sles-x86_64-cray": "fe7da6ce3df99c9aa359bfb75ab9886028679ff2d0b01d736a2e5852cec77dbc",
        "rhel-x86_64-amd": "184f199f463f14d55ee4a2c1759e3e3b32699b99781d2b81d31c69df1dc4009d",
        "sles-x86_64-amd": "2bb4e21d70c607ac46e3bf4a696cc5db225d06fe0db1c3613d8c5a61aaf362dd",
        "rhel-x86_64-gnu": "02066137721d33fc887c3b94ce4847f51bc46988d0ba2fa1c9210c7ec2c2ce0a",
        "sles-x86_64-gnu": "02f7ca146b3483fc54b75131e63974cbc3d6e2b9da05028c03f7087b2328558c",
        "rhel-x86_64-intel": "158c4b0a0d8174ec09b98faf8d23cd4f6b773a0684eb03e38fefb25ee951335d",
        "sles-x86_64-intel": "0e7d814da916795c9c3baaa7227c76af980273172654d54c0732185eeb4df9f2",
    },
    "9.2.1": {
        "rhel-x86_64-cray": "2405a14255da496a103891d601601a2306e37dc5e60771a79e4465812e90c199",
        "sles-x86_64-cray": "d487269dfca1a476d0a8bc1adf73a81165d38fbcd0c9c697b82571ac71602065",
        "rhel-x86_64-amd": "c8c18aef44d6b8155bd4e81c79cc98c817c9c9495f5fcd16d03b755e32401051",
        "sles-x86_64-amd": "beadf46826496180ec27f3c03c4ed210229b2d9cce8d71942c82ac325c2ec27d",
        "rhel-x86_64-gnu": "6f66ad5bab531b73a3edd8ee75514a6feafd78c18ca78af1b601712e42a0aa3c",
        "sles-x86_64-gnu": "6219e45210bf9461ce576706598fbbe91f548592415e76e9e59a9be23337c027",
        "rhel-x86_64-intel": "421ba7c28eac48cbbef3a656fbd852a7a3481788938f3d1e704d5e06139136f7",
        "sles-x86_64-intel": "08ce1d6ea31555427c4f31d7d403286370696076c3f9205de8e313cd785497bc",
    },
}

_GTL_VERSION_MAP: Dict = {
    "9.2.0": "0.1.7",
    "9.2.1": "0.1.7",
}


class CrayMpich(TarballPackage, CudaPackage, ROCmPackage):
    """HPE's Message Passing Interface (MPI) library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_templated_files = [  # noqa: RUF012
        "bin/mpicc",
        "bin/mpicxx",
        "bin/mpifort",
        "lib/pkgconfig/mpich.pc",
        "lib/pkgconfig/mpichf90.pc",
        "lib/pkgconfig/cray-gtl-cuda.pc",
        "lib/pkgconfig/cray-gtl-hsa.pc",
    ]

    tarball_source_prefix = "source"

    # versions & source
    for _version, targets in _VERSION_HASH_MAP.items():
        version(_version, url=_BLANK_FILE_URL, expand=False, sha256=_BLANK_FILE_HASH)
        for toolchain in _TOOLCHAINS:
            key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}-{toolchain}"
            if key not in targets:
                conflicts(f"@{_version}", when=f"toolchain={toolchain}")
            else:
                resource(
                    name=f"cray-mpich-{key}",
                    url=f"{get_base_tarball_url()}/cray-mpich/{_version}-{map_to_enterprise_distro(distro.id())}-{platform.machine()}-{toolchain}/{targets[key][:7]}.tar.gz",
                    destination="",
                    placement="source",
                    sha256=targets[key],
                    when=f"@{_version} toolchain={toolchain}",
                )

    variant(
        "toolchain",
        default="gnu",
        values=_TOOLCHAINS,
        description="Compiler toolchain used to build Cray MPICH",
    )

    # compiler requierments
    requires("%fortran=llvm-amdgpu", when="toolchain=amd")
    requires("%fortran=cray-fortran", when="toolchain=cray")
    requires("%fortran=gcc", when="toolchain=gnu")
    requires("%fortran=intel-oneapi-compilers", when="toolchain=intel")

    depends_on("cray-pmi")
    depends_on("cray-xpmem")
    depends_on("cray-libhugetlbfs")

    depends_on("libfabric")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    provides("mpi@4", when="@9:")

    @property
    def template_context(self):
        context: dict = super().template_context
        context["gtl_version"] = _GTL_VERSION_MAP[str(self.version)]
        return context

    @run_after("install")
    def clean_up_gtl(self) -> None:
        prefix_dir: Path = Path(self.prefix)
        if self.spec.satisfies("~cuda"):
            for path in prefix_dir.rglob("*cuda*"):
                if path.is_file() or path.is_symlink():
                    path.unlink()
        if self.spec.satisfies("~rocm"):
            for path in prefix_dir.rglob("*hsa*"):
                if path.is_file() or path.is_symlink():
                    path.unlink()

    def setup_run_environment(self, env):
        env.set("MPICC", join_path(self.prefix.bin, "mpicc"))
        env.set("MPICXX", join_path(self.prefix.bin, "mpicxx"))
        env.set("MPIFC", join_path(self.prefix.bin, "mpifort"))
        env.set("MPIF90", join_path(self.prefix.bin, "mpif90"))
        env.set("MPIF77", join_path(self.prefix.bin, "mpif77"))

        # dynamically loaded Cray libraries
        libs: Set = set()
        p: Path
        for lib in self.spec["cray-libhugetlbfs"].libs:
            p = Path(lib)
            libs.add(str(p.parent))
        for lib in self.spec["cray-pmi"].libs:
            p = Path(lib)
            libs.add(str(p.parent))
        for lib in self.spec["cray-xpmem"].libs:
            p = Path(lib)
            libs.add(str(p.parent))

        for lib in libs:
            env.append_path("LD_LIBRARY_PATH", lib)

    def setup_dependent_build_environment(self, env, dependent_spec):
        dependent_module = dependent_spec.package.module
        for var_name, attr_name in (
            ("MPICH_CC", "spack_cc"),
            ("MPICH_CXX", "spack_cxx"),
            ("MPICH_FC", "spack_fc"),
            ("MPICH_F90", "spack_fc"),
            ("MPICH_F77", "spack_f77"),
        ):
            if hasattr(dependent_module, attr_name):
                env.set(var_name, getattr(dependent_module, attr_name))

    def setup_dependent_package(self, module, dependent_spec):
        self.spec.mpicc = join_path(self.prefix.bin, "mpicc")
        self.spec.mpicxx = join_path(self.prefix.bin, "mpicxx")
        self.spec.mpifc = join_path(self.prefix.bin, "mpifort")
        self.spec.mpif90 = join_path(self.prefix.bin, "mpif90")
        self.spec.mpif77 = join_path(self.prefix.bin, "mpif77")

    @property
    def headers(self):
        return find_headers(["mpi"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libmpi"], root=self.prefix.lib)

    @property
    def gtl_lib(self) -> Dict:

        gtl_kinds: Dict = {
            "cuda": "libmpi_gtl_cuda",
            "rocm": "libmpi_gtl_hsa",
        }

        for accel, gtl_lib in gtl_kinds.items():
            if self.spec.satisfies(f"+{accel}"):
                gtl_shared_libraries: LibraryList = find_libraries(
                    [gtl_lib], root=self.prefix.lib, shared=True, recursive=False
                )

                if len(gtl_shared_libraries) != 1:
                    raise InstallError(
                        f"cray-mpich variant '+{accel}'"
                        " was specified and GTL support is enabled for it but"
                        f" the '{gtl_lib}' library could not be found on the file system."
                    )

                gtl_library_fullpath: str = gtl_shared_libraries[0]
                tty.debug(f"Selected GTL: {gtl_library_fullpath}")

                gtl_library_directory = Path(gtl_library_fullpath).parent
                gtl_library_name = Path(gtl_library_path.name.split("lib", 1)[1]).stem

                # Early break. Only one GTL can be active at a given time.
                return {
                    "ldflags": [
                        f"-L{gtl_library_directory}",
                        f"-Wl,-rpath,{gtl_library_directory}",
                    ],
                    "ldlibs": [f"-l{gtl_library_name}"],
                }
        return {}
