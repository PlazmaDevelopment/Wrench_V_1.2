"""
Development environment setup for Wrench Engine.

This module sets up a development environment for working with Wrench Engine.
"""

import json
import os
import platform
import subprocess
import sys
from typing import List, Dict, Any, Optional, Tuple

def setup_development_environment() -> bool:
    """
    Set up a development environment for Wrench Engine.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Setting up Wrench Engine development environment...")
    
    try:
        # Check Python version
        if not check_python_version():
            return False
        
        # Install development dependencies
        if not install_development_dependencies():
            return False
        
        # Set up development configuration
        if not setup_development_config():
            return False
        
        # Set up pre-commit hooks
        if not setup_pre_commit_hooks():
            print("Warning: Failed to set up pre-commit hooks")
        
        # Set up development tools
        if not setup_development_tools():
            print("Warning: Some development tools could not be set up")
        
        print("\nDevelopment environment setup complete!")
        print("You can now start developing Wrench Engine.")
        
        return True
        
    except Exception as e:
        print(f"Error setting up development environment: {e}")
        return False

def check_python_version(min_version: tuple = (3, 8)) -> bool:
    """Check if the Python version meets the minimum requirement."""
    if sys.version_info < min_version:
        print(f"Error: Python {'.'.join(map(str, min_version))}+ is required")
        return False
    return True

def install_development_dependencies() -> bool:
    """Install development dependencies."""
    print("\nInstalling development dependencies...")
    
    # List of development dependencies
    dev_dependencies = [
        'pytest',
        'pytest-cov',
        'black',
        'isort',
        'flake8',
        'mypy',
        'pre-commit',
        'sphinx',
        'sphinx-rtd-theme',
        'twine',
        'wheel',
        'setuptools',
        'build'
    ]
    
    try:
        # Install dependencies using pip
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ])
        
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', *dev_dependencies
        ])
        
        print("Development dependencies installed successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install development dependencies: {e}")
        return False

def setup_development_config() -> bool:
    """Set up development configuration files."""
    print("\nSetting up development configuration...")
    
    try:
        # Create .gitignore if it doesn't exist
        gitignore_path = os.path.join(os.getcwd(), '.gitignore')
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Wrench specific
*.wbuild
.cache/
.coverage
htmlcov/

# Logs
logs/
*.log

# Local development
.env
.env.local

# Build artifacts
build/
dist/
*.egg-info/
""")
        
        # Create pytest.ini if it doesn't exist
        pytest_ini_path = os.path.join(os.getcwd(), 'pytest.ini')
        if not os.path.exists(pytest_ini_path):
            with open(pytest_ini_path, 'w') as f:
                f.write("""[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --cov=wrench --cov-report=term-missing
""")
        
        # Create .flake8 if it doesn't exist
        flake8_path = os.path.join(os.getcwd(), '.flake8')
        if not os.path.exists(flake8_path):
            with open(flake8_path, 'w') as f:
                f.write("""[flake8]
max-line-length = 88
exclude = .git,__pycache__,.venv,venv
""")
        
        print("Development configuration set up successfully.")
        return True
        
    except Exception as e:
        print(f"Error setting up development configuration: {e}")
        return False

def setup_pre_commit_hooks() -> bool:
    """Set up pre-commit hooks."""
    print("\nSetting up pre-commit hooks...")
    
    try:
        # Create .pre-commit-config.yaml if it doesn't exist
        pre_commit_config = os.path.join(os.getcwd(), '.pre-commit-config.yaml')
        if not os.path.exists(pre_commit_config):
            with open(pre_commit_config, 'w') as f:
                f.write("""repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: debug-statements
    -   id: requirements-txt-fixer

-   repo: https://github.com/psf/black
    rev: 24.4.0
    hooks:
    -   id: black
        language_version: python3

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort
        name: isort (python)
        types: [python]

-   repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-bugbear]
""")
        
        # Install pre-commit hooks
        subprocess.check_call([sys.executable, '-m', 'pre-commit', 'install'])
        
        print("Pre-commit hooks set up successfully.")
        return True
        
    except Exception as e:
        print(f"Error setting up pre-commit hooks: {e}")
        return False

def setup_development_tools() -> bool:
    """Set up additional development tools."""
    print("\nSetting up development tools...")
    
    try:
        # Set up VS Code settings if .vscode directory exists
        vscode_dir = os.path.join(os.getcwd(), '.vscode')
        if not os.path.exists(vscode_dir):
            os.makedirs(vscode_dir)
            
        # Create settings.json if it doesn't exist
        settings_path = os.path.join(vscode_dir, 'settings.json')
        if not os.path.exists(settings_path):
            with open(settings_path, 'w') as f:
                json.dump({
                    "python.pythonPath": sys.executable,
                    "python.linting.enabled": True,
                    "python.linting.pylintEnabled": False,
                    "python.linting.flake8Enabled": True,
                    "python.linting.mypyEnabled": True,
                    "python.formatting.provider": "black",
                    "editor.formatOnSave": True,
                    "editor.codeActionsOnSave": {
                        "source.organizeImports": True
                    },
                    "python.testing.pytestEnabled": True,
                    "python.testing.unittestEnabled": False,
                    "python.testing.nosetestsEnabled": False,
                    "python.testing.pytestArgs": ["tests"],
                }, f, indent=4)
        
        # Set up virtual environment
        if not setup_virtual_environment():
            print("Warning: Failed to set up virtual environment")
        
        # Install project dependencies
        if not install_project_dependencies():
            print("Warning: Failed to install project dependencies")
        
        # Set up Git
        if not setup_git():
            print("Warning: Failed to set up Git")
        
        # Set up project structure
        if not setup_project_structure():
            print("Warning: Failed to set up project structure")
        
        print("Development tools set up successfully.")
        return True
        
    except Exception as e:
        print(f"Error setting up development tools: {e}")
        return False

def setup_virtual_environment(venv_name: str = '.venv') -> bool:
    """
    Set up a Python virtual environment.
    
    Args:
        venv_name: Name of the virtual environment directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nSetting up virtual environment...")
    
    try:
        # Check if virtual environment already exists
        if os.path.exists(venv_name):
            print(f"Virtual environment '{venv_name}' already exists.")
            return True
        
        # Create virtual environment
        subprocess.check_call([sys.executable, '-m', 'venv', venv_name])
        
        print(f"Virtual environment created at {os.path.abspath(venv_name)}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False

def install_project_dependencies(requirements_file: str = 'requirements-dev.txt') -> bool:
    """
    Install project dependencies from requirements file.
    
    Args:
        requirements_file: Path to requirements file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nInstalling project dependencies...")
    
    # Default requirements if requirements file doesn't exist
    default_requirements = [
        'numpy>=1.21.0',
        'pygame>=2.1.0',
        'PyOpenGL>=3.1.0',
        'PyOpenGL-accelerate>=3.1.0',
        'pillow>=8.0.0',
        'pyyaml>=5.0.0',
    ]
    
    try:
        # Create default requirements file if it doesn't exist
        if not os.path.exists(requirements_file):
            with open(requirements_file, 'w') as f:
                f.write('\n'.join(default_requirements) + '\n')
        
        # Install dependencies
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file
        ])
        
        print("Project dependencies installed successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install project dependencies: {e}")
        return False

def setup_git() -> bool:
    """
    Set up Git repository and basic configuration.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nSetting up Git...")
    
    try:
        # Check if Git is installed
        subprocess.check_call(['git', '--version'], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        
        # Initialize Git repository if it doesn't exist
        if not os.path.exists('.git'):
            subprocess.check_call(['git', 'init'])
            
            # Set up basic Git configuration
            subprocess.check_call(['git', 'config', '--local', 'user.name', 'Wrench Developer'])
            subprocess.check_call(['git', 'config', '--local', 'user.email', 'developer@example.com'])
            
            # Create initial commit
            subprocess.check_call(['git', 'add', '.'])
            subprocess.check_call(['git', 'commit', '-m', 'Initial commit'])
            
            print("Git repository initialized with initial commit.")
        else:
            print("Git repository already initialized.")
        
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Git is not installed or not in PATH. Skipping Git setup.")
        return False

def setup_project_structure() -> bool:
    """
    Set up basic project structure.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nSetting up project structure...")
    
    try:
        # Create directories
        dirs = [
            'src',
            'tests',
            'docs',
            'assets',
            'assets/fonts',
            'assets/images',
            'assets/sounds',
            'data',
            'logs'
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Create basic test file
        test_file = os.path.join('tests', 'test_example.py')
        if not os.path.exists(test_file):
            with open(test_file, 'w') as f:
                f.write('''"""Example test file."""

def test_example():
    """Example test function."""
    assert True
''')
        
        # Create README.md if it doesn't exist
        readme_file = 'README.md'
        if not os.path.exists(readme_file):
            with open(readme_file, 'w') as f:
                f.write('''# Wrench Engine Project

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Set up a virtual environment:
   ```
   python -m venv .venv
   .venv\\Scripts\\activate  # On Windows
   source .venv/bin/activate  # On Unix/macOS
   ```
3. Install dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

### Running Tests

```
pytest
```

### Development

- Format code: `black .`
- Lint code: `flake8`
- Type checking: `mypy src tests`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
''')
        
        # Create .env.example if it doesn't exist
        env_example = '.env.example'
        if not os.path.exists(env_example):
            with open(env_example, 'w') as f:
                f.write("""# Environment variables
# Copy this file to .env and update the values

# Application settings
DEBUG=True
LOG_LEVEL=INFO

# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wrench_db
DB_USER=user
DB_PASSWORD=password
""")
        
        print("Project structure set up successfully.")
        return True
        
    except Exception as e:
        print(f"Error setting up project structure: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up Wrench Engine development environment')
    args = parser.parse_args()
    
    if not setup_development_environment():
        sys.exit(1)

