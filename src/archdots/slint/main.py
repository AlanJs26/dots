from dataclasses import dataclass, field
import slint

# from slint import ListModel, Model
from slint.models import ListModel
from rich import print
from archdots.package_manager import Custom, PackageManager, package_managers
from archdots.settings import read_config
from archdots.package import Package

pm_by_name = {pm.name: pm for pm in package_managers}

PackageStruct = slint.load_file("src/archdots/slint/slint/PackagesView.slint").Package
DependencyStruct = slint.load_file(
    "src/archdots/slint/slint/PackagesView.slint"
).Dependency


@dataclass
class DependencyAttrs:
    name: str
    package_manager: str
    installed: bool = False

    def __post_init__(self):
        self.installed = self.name in pm_by_name[self.package_manager].get_installed(
            use_memo=True, by_user=False
        )


@dataclass
class PackageAttrs:
    name: str
    installed: bool
    managed: bool
    package_manager: str
    url: str = ""
    description: str = ""
    dependencies: list[DependencyAttrs] = field(default_factory=list)

    @staticmethod
    def build(package_managers: list[PackageManager]):
        pkg_attrs = []
        config = read_config()

        for pm in package_managers:
            pm.get_installed(by_user=False)

        for pm_name in config["pkgs"]:
            if pm_name == "custom":
                continue

            pkg_attrs.extend(
                [
                    PackageAttrs(
                        name=pkg_name,
                        installed=pkg_name in pm_by_name[pm_name].get_installed(True),
                        managed=True,
                        package_manager=pm_name,
                    )
                    for pkg_name in config["pkgs"][pm_name]
                ]
            )

        for pm in package_managers:
            if isinstance(pm, Custom):
                pkg_attrs.extend(
                    [
                        PackageAttrs(
                            name=pkg.name,
                            installed=pkg.check(supress_output=True),
                            managed=pkg.name in config["pkgs"][pm.name],
                            package_manager=pm.name,
                            description=pkg.description,
                            url=pkg.url,
                            dependencies=[
                                DependencyAttrs(
                                    name=dep.rsplit(":")[1],
                                    package_manager=dep.rsplit(":")[0],
                                )
                                for dep in pkg.depends
                            ],
                        )
                        for pkg in pm.get_packages()
                    ]
                )
            else:
                pkg_attrs.extend(
                    [
                        PackageAttrs(
                            name=pkg_name,
                            installed=True,
                            managed=False,
                            package_manager=pm.name,
                        )
                        for pkg_name in set(pm.get_installed(True)).difference(
                            config["pkgs"][pm.name]
                        )
                    ]
                )
        return pkg_attrs


class App(slint.load_file("src/archdots/slint/slint/main.slint").AppWindow):

    def __init__(self):
        super().__init__()
        self.packages = PackageAttrs.build(package_managers)
        self.packages_model = ListModel(self.PackageManager.packages)
        self.update_packages()
        self.PackageManager.packages = self.packages_model

    @slint.callback(global_name="PackageManager", name="update_packages")
    def update_packages(self):
        def filter_packages(pkg_attr):
            return (
                (
                    self.PackageManager.installed_state
                    and self.PackageManager.managed_state
                )
                or (
                    pkg_attr.installed == self.PackageManager.installed_state
                    and pkg_attr.managed == self.PackageManager.managed_state
                )
            ) and (
                (
                    self.PackageManager.custom_state
                    and pkg_attr.package_manager == "custom"
                )
                or (
                    self.PackageManager.pacman_state
                    and pkg_attr.package_manager == "pacman"
                )
                or (
                    self.PackageManager.winget_state
                    and pkg_attr.package_manager == "winget"
                )
            )

        def build_dependency(dep):
            return {
                "name": dep.name,
                "package_manager": dep.package_manager,
                "installed": dep.installed,
            }

        def build_package(pkg_attr, index):
            return PackageStruct(
                name=pkg_attr.name,
                description=pkg_attr.description,
                installed=pkg_attr.installed,
                managed=pkg_attr.managed,
                package_manager=pkg_attr.package_manager,
                url=pkg_attr.url,
                index=index,
                dependencies=ListModel(
                    [build_dependency(dep) for dep in pkg_attr.dependencies]
                ),
            )

        self.packages_model.list = [
            build_package(pkg_attr, i)
            for i, pkg_attr in enumerate(self.packages)
            if filter_packages(pkg_attr)
        ]

        self.PackageManager.installed_num = len(
            [pkg for pkg in self.packages if pkg.installed]
        )
        self.PackageManager.managed_num = len(
            [pkg for pkg in self.packages if pkg.managed]
        )
        self.PackageManager.filtered_length = len(self.packages_model.list)

        for i in range(len(self.packages)):
            self.packages_model.notify_row_changed(i)


def main_gui():
    app = App()
    app.run()
