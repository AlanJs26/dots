"""Abstract base class and utilities for package managers."""

from abc import ABC, abstractmethod
from typing import Any
from archdots.utils.decorators import SingletonMeta


class PackageManager(ABC, metaclass=SingletonMeta):
    """Abstract base class for package manager implementations.
    
    Each package manager (pacman, winget, scoop, etc.) inherits from this class
    and implements the required abstract methods.
    """

    def __init__(self, name: str) -> None:
        """Initialize package manager.
        
        Args:
            name: Package manager name (e.g., 'pacman', 'winget', 'scoop')
        """
        self.name = name

    @abstractmethod
    def install(self, packages: list[str], force: bool = False) -> bool:
        """Install packages.
        
        Args:
            packages: List of package names to install
            force: Force installation even if package exists
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def uninstall(self, packages: list[str]) -> bool:
        """Uninstall packages.
        
        Args:
            packages: List of package names to uninstall
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this package manager is available on the system.
        
        Returns:
            True if package manager is installed and available, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_installed(self, use_memo: bool = False, by_user: bool = True) -> list[str]:
        """Get list of installed packages.
        
        Args:
            use_memo: Use cached result if available
            by_user: Filter to user-installed packages
            
        Returns:
            List of installed package names
        """
        raise NotImplementedError
