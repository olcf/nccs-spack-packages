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
    "0.3.1": {
        "rhel-x86_64": "a84070110b2bb892bd506b670fd455a6408c6ff33d4f5e3eeadff74f2c55080f",
        "sles-x86_64": "ea648a13c05a248b853d5fd4654ee4fd4f38701747f72c5a44bdbe9f6463c5e1",
    },
}


class CrayDsmml(TarballPackage):
    """HPE's Distributed Symmetric Memory Management Library (DSMML)."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-dsmml/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    tarball_templated_files = ["lib/pkgconfig/dsmml.pc"]  # noqa: RUF012

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    @property
    def headers(self):
        return find_headers(["dsmml"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libdsmml"], root=self.prefix.lib)
