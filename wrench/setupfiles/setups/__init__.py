"""
Wrench Engine Setup Scripts

This package contains various setup scripts for Wrench Engine.
"""

__all__ = [
    'create_project',
    'setup_development_environment',
    'configure_ide',
    'install_dependencies'
]

def create_project(project_name: str, template: str = 'basic') -> bool:
    """
    Create a new Wrench project.
    
    Args:
        project_name: Name of the project to create
        template: Template to use for the project
        
    Returns:
        bool: True if successful, False otherwise
    """
    from .project_setup import create_project as _create_project
    return _create_project(project_name, template)

def setup_development_environment() -> bool:
    """
    Set up a development environment for Wrench Engine.
    
    Returns:
        bool: True if successful, False otherwise
    """
    from .dev_setup import setup_development_environment as _setup_dev_env
    return _setup_dev_env()

def configure_ide(ide: str = 'vscode') -> bool:
    """
    Configure an IDE for Wrench Engine development.
    
    Args:
        ide: IDE to configure ('vscode', 'pycharm', 'sublime')
        
    Returns:
        bool: True if successful, False otherwise
    """
    from .ide_setup import configure_ide as _configure_ide
    return _configure_ide(ide)

def install_dependencies() -> bool:
    """
    Install all required dependencies for Wrench Engine.
    
    Returns:
        bool: True if successful, False otherwise
    """
    from .dependencies import install_dependencies as _install_deps
    return _install_deps()
