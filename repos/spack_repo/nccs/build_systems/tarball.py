# Copyright ORNL

import os
import platform
from pathlib import Path
from typing import Dict, List

import spack.store as spack_store
from spack.error import SpecError
from spack.package import (
    BuilderWithDefaults,
    PackageBase,
    Prefix,
    Spec,
    build_system,
    depends_on,
    install_tree,
    redistribute,
    register_builder,
    requires,
    variant,
    when,
    which,
)
from spack.vendor import distro
from spack.vendor.jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from spack.vendor.typing_extensions import Literal

ELFCLASS32: int = 1
ELFCLASS64: int = 2
ELFDATA2LSB: int = 1
ELFDATA2MSB: int = 2
ET_EXEC: int = 2
ET_DYN: int = 3


def is_elf_with_rpath(path: Path) -> bool:
    """Return whether a path is an ELF file type that can contain a RPATH/RUNPATH."""
    if not path.is_file() or path.is_symlink():
        return False

    try:
        with path.open("rb") as f:
            header: bytes = f.read(20)

        if len(header) < 20 or header[:4] != b"\x7fELF":
            return False

        elf_class: int = header[4]
        elf_data: int = header[5]

        if elf_class not in (ELFCLASS32, ELFCLASS64):
            return False

        byteorder: Literal["little", "big"]  # noqa: F821, UP037
        if elf_data == ELFDATA2LSB:
            byteorder = "little"
        elif elf_data == ELFDATA2MSB:
            byteorder = "big"
        else:
            return False

        # e_type is the 16-bit field at bytes 16--17.
        elf_type: int = int.from_bytes(header[16:18], byteorder=byteorder)

        return elf_type in (ET_EXEC, ET_DYN)

    except OSError:
        return False


def map_to_enterprise_distro(distribution: str) -> str:
    if distribution == "almalinux" or distribution == "rocky":
        return "rhel"
    else:
        return distribution


def get_base_tarball_url() -> str:
    if "NCCS_BASE_TARBALL_URL" in os.environ:
        return str(os.getenv("NCCS_BASE_TARBALL_URL"))
    raise ValueError("environment variable 'NCCS_BASE_TARBALL_URL' is not set")


class TarballPackage(PackageBase):
    """Specialized class for installing tarballs."""

    tarball_url_template: str = ""
    tarball_extra_context: Dict = {}  # noqa: RUF012
    tarball_templated_files: List[str] = []  # noqa: RUF012
    tarball_source_prefix: str = ""

    build_system_class = "TarballPackage"

    build_system("tarball")

    # do not allow tarballs to be pushed to mirrors/build caches
    redistribute(source=False, binary=False)

    # tarballs only work on Linux
    requires("platform=linux", msg="tarballs are only for linux")

    with when("build_system=tarball"):
        # common variants
        variant(
            "rpath",
            default=True,
            description="Set the rpath for eligible ELF files",
        )
        variant(
            "static",
            default=True,
            description="Keep static libraries",
        )

        # build dependencies
        depends_on("patchelf", type="build", when="+rpath")

    def url_for_version(self, version):
        return Template(self.tarball_url_template).render(**self.template_context)

    @property
    def template_context(self) -> Dict:
        # arch, distro and version
        context: Dict = {
            "arch": platform.machine(),
            "distro": {
                "name": map_to_enterprise_distro(distro.id()),
                "version": distro.version(),
            },
            "version": str(self.version),
        }

        # prefix
        try:
            context["prefix"] = str(self.prefix)
        except SpecError:
            pass

        # c, cxx and fortran (actual compilers not compiler-wrappers)
        if "c" in self.spec:
            context["c"] = str(self.spec["c"].package.cc)
        if "cxx" in self.spec:
            context["cxx"] = str(self.spec["cxx"].package.cxx)
        if "fortran" in self.spec:
            context["fortran"] = str(self.spec["fortran"].package.fortran)

        # dependencies
        for d in self.spec.dependencies():
            try:  # jinja interpets "-" as the subtraction operator
                context[d.name.replace("-", "_")] = {"prefix": d.prefix}
            except SpecError:
                pass

        # custom context
        context.update(self.tarball_extra_context)

        return context

    @property
    def valid_rpaths(self) -> List[str]:
        spack_install_root: Path = Path(spack_store.STORE.root).resolve()

        paths: List[str] = []
        for p in self.rpath:
            path: Path = Path(p)

            if not path.exists():
                continue

            try:
                path.relative_to(spack_install_root)
            except ValueError:
                continue

            paths.append(str(path))

        return paths


@register_builder("tarball")
class TarballBuilder(BuilderWithDefaults):
    """The tarball builder unpacks tarballs and preforms various edits."""

    phases = ("install",)

    def install(self, pkg: TarballPackage, spec: Spec, prefix: Prefix):
        prefix_dir: Path = Path(prefix)

        # install files
        install_tree(str(Path(pkg.stage.source_path) / pkg.tarball_source_prefix), prefix_dir)

        # generate templated files
        jinja_env: Environment = Environment(
            loader=FileSystemLoader(prefix_dir),
            undefined=StrictUndefined,
            autoescape=False,
        )
        for f in pkg.tarball_templated_files:
            template: Template = jinja_env.get_template(f)
            rendered: str = template.render(**pkg.template_context)
            (prefix_dir / f).write_text(rendered, encoding="utf-8")

        # set rpaths
        if spec.satisfies("+rpath"):
            patchelf: Executable = which("patchelf", required=True)
            for p in prefix_dir.rglob("*"):
                if is_elf_with_rpath(p):
                    patchelf(
                        "--force-rpath",
                        "--add-rpath",
                        ":".join(pkg.valid_rpaths),
                        str(p),
                    )

        # remove static libraries
        if spec.satisfies("~static"):
            for p in prefix_dir.rglob("*"):
                if (p.is_file() or p.is_symlink()) and str(p).endswith(".a"):
                    p.unlink()
