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
    "2.24": {
        "rhel-x86_64": "b10f77f6ffc0a5c64542b37d9485411ec827635468a402e1d05dbe06aa90e07e",
        "sles-x86_64": "99e485dddbee829dc501163b929b7b2f332beeff462d978bf3a41222630b7fac",
    },
}


class CrayLibhugetlbfs(TarballPackage):
    """HPE's libhugetlbfs library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-libhugetlbfs/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    @property
    def headers(self):
        return find_headers(["hugetlbfs"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libhugetlbfs", "libhugetlbfs_privutils"], root=self.prefix.lib64)
