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
    "11.8.0": {
        "rhel-x86_64": "537383ad441e85b1f4f57d08b0447b2eb29b701ee2bafb7cdb11a6f78c8e20a1",
        "sles-x86_64": "64b4772023614b239e19f817a1354473f626bfaa827866f9b51335f9d6ab599a",
    },
}


class CrayShmem(TarballPackage):
    """HPE's Shared Memory (SHMEM) library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-shmem/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    tarball_templated_files = [  # noqa: RUF012
        "lib64/pkgconfig/sma.pc",
        "lib64/pkgconfig/smaf.pc",
    ]

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    depends_on("libfabric")

    depends_on("cray-dsmml")

    @property
    def headers(self):
        return find_headers(
            [
                "shmem",
                "shmemx",
                "pshmem",
                "pshmemx",
            ],
            self.prefix.include,
        )

    @property
    def libs(self):
        return find_libraries(["libsma"], root=self.prefix.lib64)
