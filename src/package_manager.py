import subprocess
from abc import abstractmethod
from src.package import get_packages, Package, install_packages, uninstall_packages
from src.constants import MODULE_PATH
from pathlib import Path


class SingletonMeta(type):
    """
    Metaclasse para implementar o padrão Singleton.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # Cria a instância e armazena no dicionário
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class PackageManagerException(Exception):
    pass


class PackageManager(metaclass=SingletonMeta):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def install(self, packages: list[str]) -> bool:
        raise NotImplemented

    @abstractmethod
    def uninstall(self, packages: list[str]) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplemented

    @abstractmethod
    def get_installed(self) -> list[str]:
        raise NotImplemented


class Pacman(PackageManager):
    def __init__(self, aur_helper="yay") -> None:
        super().__init__("pacman")
        self.aur_helper = aur_helper

    def get_installed(self) -> list[str]:
        process = subprocess.Popen(
            f"{self.aur_helper} -Qe|awk '{{print $1}}'",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            text=True,
        )
        if not process.stdout:
            if process.stderr:
                print(process.stderr.read())
            raise PackageManagerException("could not run 'pacman -Qe'")

        return [line.strip() for line in process.stdout.readlines()]

    def install(self, packages: list[str]) -> bool:
        process = subprocess.Popen(
            f"{self.aur_helper} -Sy {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        process = subprocess.Popen(
            f"{self.aur_helper} -R {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        from shutil import which

        return which(self.aur_helper.split()[-1]) is not None


class Custom(PackageManager):
    def __init__(self) -> None:
        super().__init__("custom")

    @staticmethod
    def _filter_custom_packages(
        target_pkgs: list[str] | list[Package], all_packages: list[Package]
    ) -> list[Package]:
        if any(isinstance(pkg, Package) for pkg in target_pkgs):
            return target_pkgs  # type: ignore
        else:
            return list(filter(lambda pkg: pkg.name in target_pkgs, all_packages))

    def get_packages(self) -> list[Package]:
        return get_packages(str(Path(MODULE_PATH) / "packages"))

    def get_installed(self) -> list[str]:
        custom_packages = self.get_packages()

        return [pkg.name for pkg in custom_packages if pkg.check(supress_output=True)]

    def install(self, packages: list[str] | list[Package]) -> bool:
        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        install_packages(filtered_packages, all_packages)

        return True

    def uninstall(self, packages: list[str] | list[Package]) -> bool:
        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        uninstall_packages(filtered_packages, all_packages)

        return True

    def is_available(self) -> bool:
        return True


package_managers = [Pacman(), Custom()]
