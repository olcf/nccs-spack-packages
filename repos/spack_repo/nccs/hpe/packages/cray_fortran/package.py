# Copyright ORNL

import platform
from pathlib import Path
from typing import Dict, Optional

from spack.package import *
from spack.vendor import distro
from spack_repo.builtin.build_systems.compiler import CompilerPackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage
from spack_repo.nccs.build_systems.tarball import (
    TarballPackage,
    get_base_tarball_url,
    map_to_enterprise_distro,
)

_VERSION_HASH_MAP: Dict = {
    "22.0.0": {
        "rhel-x86_64": "8da05bbdaae6ca9104429328388b7d86a3cc5514b59d790c290efaf5e2404978",
        "sles-x86_64": "64b230d99776af99634b84697ff3b38f1a895d76c2f5904ae2e796933ebe6357",
    },
}


class CrayFortran(TarballPackage, CudaPackage, ROCmPackage, CompilerPackage):
    """HPE's Fortran compiler."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-fortran/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    compiler_languages = ["fortran"]  # noqa: RUF012

    fortran_names = ["crayftn"]  # noqa: RUF012

    compiler_version_argument = "--version"
    compiler_version_regex = r"Cray Fortran : Version ([^\s]+) \("

    compiler_wrapper_link_paths = {  # noqa: RUF012
        "fortran": "cce/crayftn",
    }

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    variant(
        "shmem",
        default=False,
        description="Include SHMEM libraries",
    )

    depends_on("cray-shmem", when="+shmem")
    depends_on("cray-pmi", when="+shmem")

    provides("fortran")

    def _fortran_path(self):
        return str(Path(self.prefix) / "bin/crayftn")

    @run_after("install")
    def clean_up_extra_libs(self):
        prefix_dir: Path = Path(self.prefix)
        if self.spec.satisfies("~cuda"):
            for path in (prefix_dir / f"cce/{platform.machine()}/lib").glob("libcrayacc.*"):
                if path.is_file() or path.is_symlink():
                    path.unlink()
        if self.spec.satisfies("~rocm"):
            for path in (prefix_dir / f"cce/{platform.machine()}/lib").glob("libcrayacc_amdgpu*"):
                if path.is_file() or path.is_symlink():
                    path.unlink()
        if self.spec.satisfies("~shmem"):
            for path in (prefix_dir / f"cce/{platform.machine()}/lib").glob("libpgas-shmem*"):
                if path.is_file() or path.is_symlink():
                    path.unlink()
