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
    "6.1.18": {
        "rhel-x86_64": "8bd73fe9e35ef58e4e710a693af97d585b0235da3dd334301ad3cb50be4f1cf6",
        "sles-x86_64": "b794d03eb8c6aa37c480c841fc037699ba102171658051523b40a3516fadb1d8",
    },
}


class CrayPmi(TarballPackage):
    """HPE's Process Management Interface (PMI) library."""

    homepage = "https://h41374.www4.it.hpe.com/docs/latest/index.html"

    supplier = "Organization: Hewlett Packard Enterprise"

    maintainers("AcerP-py", "jfillers")

    tarball_url_template = (
        get_base_tarball_url()
        + "/cray-pmi/{{ version }}-{{ distro.name }}-{{ arch }}/{{ short_hash }}.tar.gz"
    )

    tarball_templated_files = ["lib/pkgconfig/cray-pmi.pc"]  # noqa: RUF012

    for _version, targets in _VERSION_HASH_MAP.items():
        key: str = f"{map_to_enterprise_distro(distro.id())}-{platform.machine()}"
        _hash: Optional[str] = targets.get(key)
        if _hash:
            tarball_extra_context: Dict = {"short_hash": _hash[:7]}
            version(_version, sha256=_hash)

    depends_on("cray-libpals")

    @property
    def headers(self):
        return find_headers(["pmi", "pmi2"], self.prefix.include)

    @property
    def libs(self):
        return find_libraries(["libpmi", "libpmi2"], root=self.prefix.lib)
