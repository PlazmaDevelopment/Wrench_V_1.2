"""
Compatibility module for Wrench Engine.

This module handles system compatibility checks and fixes for different platforms.
"""

import os
import sys
import platform
import subprocess
import ctypes
import shutil
from typing import Dict, List, Tuple, Optional

def check_requirements() -> Dict[str, bool]:
    """
    Check if the system meets the minimum requirements for Wrench Engine.
    
    Returns:
        Dict containing the status of each requirement check.
    """
    requirements = {
        'python_version': check_python_version(),
        'opengl_version': check_opengl_version(),
        'ram': check_ram(),
        'disk_space': check_disk_space(),
        'gpu': check_gpu(),
        'dependencies': check_dependencies(),
        'permissions': check_permissions()
    }
    
    # Overall status
    requirements['all_passed'] = all(requirements.values())
    
    return requirements

def check_python_version(min_version: Tuple[int, int, int] = (3, 8, 0)) -> bool:
    """Check if the Python version meets the minimum requirement."""
    return sys.version_info >= min_version

def check_opengl_version(min_version: Tuple[int, int] = (3, 3)) -> bool:
    """Check if the system supports the minimum required OpenGL version."""
    try:
        import OpenGL
        from OpenGL import GL
        
        # Get OpenGL version
        version_str = GL.glGetString(GL.GL_VERSION).decode('utf-8')
        version_parts = version_str.split('.') if version_str else ['0', '0']
        
        # Convert to integers for comparison
        major = int(version_parts[0]) if version_parts else 0
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        return (major, minor) >= min_version
    except Exception:
        return False

def check_ram(min_gb: int = 4) -> bool:
    """Check if the system has at least the minimum required RAM."""
    try:
        import psutil
        return psutil.virtual_memory().total >= (min_gb * 1024 ** 3)
    except Exception:
        return False

def check_disk_space(min_gb: int = 2, path: str = '.') -> bool:
    """Check if there's enough disk space available."""
    try:
        total, used, free = shutil.disk_usage(path)
        return free >= (min_gb * 1024 ** 3)
    except Exception:
        return False

def check_gpu() -> bool:
    """Check if the system has a compatible GPU."""
    try:
        # Try to import GPU info
        import GPUtil
        gpus = GPUtil.getGPUs()
        return len(gpus) > 0
    except ImportError:
        # Fallback to checking OpenGL vendor
        try:
            from OpenGL import GL
            vendor = GL.glGetString(GL.GL_VENDOR)
            return vendor is not None
        except:
            return False

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    required = ['numpy', 'pygame', 'PyOpenGL', 'PyOpenGL_accelerate']
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            return False
    
    return True

def check_permissions() -> bool:
    """Check if we have the necessary permissions."""
    try:
        # Try to create a temporary file in the installation directory
        temp_file = os.path.join(os.path.dirname(__file__), '.temp_permission_check')
        with open(temp_file, 'w') as f:
            f.write('test')
        os.remove(temp_file)
        return True
    except (IOError, OSError):
        return False

def fix_import_issues() -> None:
    """Fix common import issues."""
    # Add the Wrench directory to the Python path
    wrench_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if wrench_dir not in sys.path:
        sys.path.insert(0, wrench_dir)
    
    # Set environment variables for libraries
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    os.environ['PYGAME_BLEND_ALPHA_SDL2'] = '1'

def fix_path_issues() -> None:
    """Fix common path-related issues."""
    # Add common DLL directories to the PATH on Windows
    if platform.system() == 'Windows':
        system_path = os.environ.get('PATH', '').split(os.pathsep)
        
        # Common directories that might contain required DLLs
        common_dirs = [
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'SysWOW64'),
            os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Common Files'),
            os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'), 'Common Files'),
        ]
        
        # Add directories to PATH if they exist and aren't already in PATH
        for dir_path in common_dirs:
            if os.path.exists(dir_path) and dir_path not in system_path:
                system_path.append(dir_path)
        
        # Update PATH
        os.environ['PATH'] = os.pathsep.join(system_path)

def install_missing_dependencies() -> bool:
    """Install missing Python dependencies."""
    try:
        import pip
        
        # List of required packages
        requirements = [
            'numpy',
            'pygame',
            'PyOpenGL',
            'PyOpenGL-accelerate',
            'psutil',
            'GPUtil',
            'winshell',
            'pywin32'
        ]
        
        # Install each package
        for package in requirements:
            try:
                __import__(package.split('>=')[0].split('==')[0])
            except ImportError:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        
        return True
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        return False

def run_as_admin():
    """Run the current script with administrator privileges."""
    if platform.system() != 'Windows':
        return False
    
    try:
        # Check if already running as admin
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
            
        # Re-run with admin rights
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])
        
        ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, params, None, 1
        )
        
        # Exit the current instance
        sys.exit(0)
    except Exception as e:
        print(f"Failed to run as admin: {e}")
        return False

def fix_file_associations():
    """Set up file associations for Wrench Engine files."""
    if platform.system() != 'Windows':
        return False
    
    try:
        import winreg
        
        # Define file extensions to associate
        extensions = {
            '.wrench': 'Wrench.Project',
            '.wscene': 'Wrench.Scene',
            '.wprefab': 'Wrench.Prefab'
        }
        
        # Get the path to the Python executable
        python_exe = sys.executable
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'wrench',
            'main.py'
        )
        
        # Open the registry key for file associations
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, 'Wrench.Project') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, 'Wrench Project File')
            
            # Set icon
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets',
                'wrench.ico'
            )
            winreg.SetValueEx(key, 'DefaultIcon', 0, winreg.REG_SZ, f'"{icon_path}"')
            
            # Set open command
            with winreg.CreateKey(key, 'shell\open\command') as cmd_key:
                winreg.SetValue(
                    cmd_key,
                    '',
                    winreg.REG_SZ,
                    f'"{python_exe}" "{script_path}" "%1"'
                )
        
        # Associate file extensions
        for ext, prog_id in extensions.items():
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ext) as key:
                winreg.SetValue(key, '', winreg.REG_SZ, prog_id)
        
        # Notify the system of the changes
        ctypes.windll.shell32.SHChangeNotify(
            0x08000000,  # SHCNE_ASSOCCHANGED
            0x00001000,  # SHCNF_IDLIST
            0, 0
        )
        
        return True
    except Exception as e:
        print(f"Failed to set file associations: {e}")
        return False
