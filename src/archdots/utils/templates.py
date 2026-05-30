def generate_pkgbuild_template(
    pkg_name: str,
    pkg_description: str,
    pkg_dependencies: list[str],
    platform: str,
    pkg_url: str = "",
    pkg_sources: list[str] | None = None,
    is_health_script: bool = False,
) -> str:
    pkg_sources = pkg_sources or []
    item_type = "health script" if is_health_script else "package"
    action_install = "configure the health script" if is_health_script else "install the package on the system"
    action_uninstall = "unconfigure the health script" if is_health_script else "uninstall the package from the system"
    action_check_success = "configured" if is_health_script else "installed on system"
    action_check_fail = "unconfigured" if is_health_script else "uninstalled"
    
    return f'''
description='{pkg_description.replace("'", "\\'")}'
url='{pkg_url.replace("'", "\\'")}'
depends=({' '.join(f"'{dep}'" for dep in pkg_dependencies)})
source=({' '.join(f"'{source}'" for source in pkg_sources)})
# source_on_check=false
# asks user for elevated privileges
# elevated=false
# make this {item_type} platform specific. Examples: linux, windows, archlinux, ubuntu
platform='{platform}'

# All items of source will be downloaded and extracted (when necessary)
# all downloaded (or extracted folders) are stored inside ${{sourced[@]}}
# This script runs inside a folder over ~/.cache/archdots/pkgname, where all sources are downloaded
#
# $PKGPATH has the path to folder containing this file 

# You can add the suffix "_powershell" to the functions in order to run them using powershell

# This function is used to {action_install}
install() {{
    echo "message from install() of {pkg_name}" 
}}

# This function is used to {action_uninstall}
uninstall() {{
    echo "message from uninstall() of {pkg_name}" 
}}

# This function should end with exit code 0 when the {item_type} is {action_check_success}
# and end with exit code 1 when it is {action_check_fail}
check() {{
    echo "message from check() of {pkg_name}" 
}}
'''.strip()
