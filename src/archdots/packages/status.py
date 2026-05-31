from archdots.packages.dependencies import split_packages_by_pm


def check_packages(packages: list[str], use_memo=False) -> dict[str, bool]:
    pkgs_by_pm = split_packages_by_pm(packages)

    statuses: dict[str, bool] = {}
    for pm, pkgs in pkgs_by_pm.items():
        for pkg in pkgs:
            statuses[pkg] = pm.is_installed(pkg, use_memo)

    return statuses
