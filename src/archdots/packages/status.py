from multiprocessing.pool import ThreadPool
from archdots.packages.dependencies import split_packages_by_pm
from archdots.packages.managers.base import PackageManager


def _get_installed_wrapper(pm_data):
    pm, use_memo, by_user = pm_data
    return pm.name, pm.get_installed(use_memo, by_user=by_user)


def bulk_get_installed(package_managers: list[PackageManager], use_memo: bool = False, by_user: bool = True) -> dict[str, list[str]]:
    """Fetch installed packages from multiple managers in parallel using threads.
    
    Threads are used instead of processes to share the in-memory memoization cache.
    
    Args:
        package_managers: List of PackageManager instances
        use_memo: Whether to use cached results
        by_user: Filter to user-installed packages
        
    Returns:
        Dictionary mapping package manager names to lists of installed package names
    """
    with ThreadPool() as pool:
        results = pool.map(_get_installed_wrapper, [(pm, use_memo, by_user) for pm in package_managers])
    
    return dict(results)


def check_packages(packages: list[str], use_memo=False) -> dict[str, bool]:
    pkgs_by_pm = split_packages_by_pm(packages)

    statuses: dict[str, bool] = {}
    for pm, pkgs in pkgs_by_pm.items():
        for pkg in pkgs:
            statuses[pkg] = pm.is_installed(pkg, use_memo)

    return statuses
