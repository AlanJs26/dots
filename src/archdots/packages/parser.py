import os
from pathlib import Path
from typing import Any

from archdots.core.exceptions import PackageException


def parse_package_lark(pkgbuild_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    from archdots.package_parser import parse_from_path

    items, funcs = parse_from_path(pkgbuild_path)

    fields_dict = {item.key: item.value for item in items}
    func_names = [func.name for func in funcs]

    return fields_dict, func_names


def package_from_path(folder_path: str | Path, package_cls):
    folder_path = Path(folder_path)
    pkg_name = folder_path.stem
    pkgbuild_path = folder_path / "PKGBUILD"

    fields_dict, funcs = parse_package_lark(pkgbuild_path)

    # Merge platform-specific dependencies
    from archdots.core.platforms.registry import get_current_platform

    current_platform = get_current_platform()

    for key in list(fields_dict.keys()):
        if key.endswith("_depends"):
            plat_name = key.removesuffix("_depends")
            if current_platform.supports(plat_name):
                if "depends" not in fields_dict:
                    fields_dict["depends"] = []
                # Ensure it's a list (array in PKGBUILD)
                val = fields_dict[key]
                if isinstance(val, list):
                    fields_dict["depends"].extend(val)
                else:
                    fields_dict["depends"].append(str(val))
            del fields_dict[key]

    funcs = [f.removesuffix("_powershell") for f in funcs]

    known_fields = ["depends", "description", "source", "url"]
    known_funcs = [
        "check",
        "install",
        "uninstall",
    ]

    if missing_fields := set(known_fields).difference(fields_dict.keys()):
        raise PackageException(
            f"missing fields: {list(missing_fields)}",
            pkg_name=pkg_name,
            pkgbuild=str(pkgbuild_path),
        )
    if missing_funcs := set(known_funcs).difference(funcs):
        raise PackageException(
            f"missing functions: {list(missing_funcs)}",
            pkg_name=pkg_name,
            pkgbuild=str(pkgbuild_path),
        )

    fields_dict["depends"] = [
        ("custom:" + dep if ":" not in dep else dep) for dep in fields_dict["depends"]
    ]

    if "platform" in fields_dict:
        from archdots.core.platforms.registry import get_platform_by_name

        if not get_platform_by_name(fields_dict["platform"]):
            raise PackageException(
                f'invalid platform: {fields_dict["platform"]}',
                pkg_name=pkg_name,
                pkgbuild=str(pkgbuild_path),
            )

    if "elevated" in fields_dict and str(fields_dict["elevated"]).lower() not in [
        "true",
        "false",
    ]:
        raise PackageException(
            f'invalid value for field elevated: {fields_dict["elevated"]}',
            pkg_name=pkg_name,
            pkgbuild=str(pkgbuild_path),
        )

    # Filter fields_dict to only include fields known by the Package dataclass
    allowed_fields = [
        "description",
        "url",
        "depends",
        "source",
        "platform",
        "source_on_check",
        "elevated",
    ]
    filtered_fields = {k: v for k, v in fields_dict.items() if k in allowed_fields}

    return package_cls(
        name=pkg_name,
        pkgbuild=str(pkgbuild_path),
        available_functions=funcs,
        **filtered_fields,
    )


def get_packages(folder: str | Path, package_from_path_fn, ignore_platform=False):
    filtered_packages = []
    for root, dirs, files in os.walk(folder, topdown=True):
        if "PKGBUILD" not in files:
            continue
        dirs[:] = []
        filtered_packages.append(root)

    packages = [
        package_from_path_fn(pkgbuild_path) for pkgbuild_path in filtered_packages
    ]
    if ignore_platform:
        return packages

    from archdots.core.platforms.registry import get_current_platform

    current_platform = get_current_platform()
    return list(filter(lambda pkg: current_platform.supports(pkg.platform), packages))
