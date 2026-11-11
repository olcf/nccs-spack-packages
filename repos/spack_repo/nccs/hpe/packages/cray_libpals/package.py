# Copyright ORNL

import platform
from typing import Dict, Optional

from spack.package import *
from spack.vendor import distro
from spack_repo.nccs.build_systems.tarball import (
    TarballPackage,
    get_base_tarball_url,
    map_to_enterprise_distro,
)

_VERSION_HASH_MAP: Dict = {
    "1.9.2": {
        "rhel-x86_64": "520743b524599fa59274847533d1bd63c65c9948019d6c12c8cd09e3a31780f4",
        "sles-x86_64": "0713625d5496bfff7848a938b6543f3852281456ed0d8b3a0e2232351889ea42",
    },
}


class CrayLibpals(TarballPackage):
    """HPE's Parallel Application Launch Service (PALS) library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-libpals/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    tarball_templated_files = ["lib/pkgconfig/libpals.pc"]  # noqa: RUF012

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    @property
    def headers(self):
        return find_headers(["pals"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libpals"], root=self.prefix.lib)
