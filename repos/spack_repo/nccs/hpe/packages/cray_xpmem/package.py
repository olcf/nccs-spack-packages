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
    "1.0.2": {
        "rhel-x86_64": "cda88cd1a3b8676ac6626cab9aa7d18c3940c2a511908ab10d9619d3f9fb5528",
        "sles-x86_64": "485a9e202f60fa8e1246766f0ffa83f01eec2adb284b29c8ae9eb9b70b6ef997",
    },
}


class CrayXpmem(TarballPackage):
    """HPE's Cross-memory Attach (XPMEM) library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-xpmem/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    tarball_templated_files = ["lib64/pkgconfig/xpmem.pc"]  # noqa: RUF012

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    @property
    def headers(self):
        return find_headers(["xpmem"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libxpmem"], root=self.prefix.lib64)
