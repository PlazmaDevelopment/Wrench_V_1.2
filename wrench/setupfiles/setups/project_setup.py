"""
Project setup module for Wrench Engine.

This module provides functionality to create new Wrench projects.
"""

import os
import shutil
import json
from typing import Dict, Any

def create_project(project_name: str, template: str = 'basic') -> bool:
    """
    Create a new Wrench project.
    
    Args:
        project_name: Name of the project to create
        template: Template to use for the project
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate project name
        if not project_name or not isinstance(project_name, str):
            raise ValueError("Project name must be a non-empty string")
        
        # Get template directory
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'templates',
            template
        )
        
        if not os.path.exists(template_dir):
            raise ValueError(f"Template '{template}' not found")
        
        # Create project directory
        project_dir = os.path.abspath(project_name)
        if os.path.exists(project_dir):
            raise FileExistsError(f"Directory '{project_dir}' already exists")
        
        os.makedirs(project_dir, exist_ok=True)
        
        # Copy template files
        copy_template_files(template_dir, project_dir, project_name)
        
        # Update project configuration
        update_project_config(project_dir, project_name, template)
        
        print(f"Successfully created project '{project_name}'")
        print(f"Project directory: {project_dir}")
        
        return True
        
    except Exception as e:
        print(f"Error creating project: {e}")
        # Clean up if something went wrong
        if 'project_dir' in locals() and os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        return False

def copy_template_files(template_dir: str, project_dir: str, project_name: str) -> None:
    """Copy template files to the project directory."""
    # Copy all files from template directory
    for item in os.listdir(template_dir):
        s = os.path.join(template_dir, item)
        d = os.path.join(project_dir, item)
        
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    # Create necessary directories
    os.makedirs(os.path.join(project_dir, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'scenes'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'scripts'), exist_ok=True)

def update_project_config(project_dir: str, project_name: str, template: str) -> None:
    """Update the project configuration file."""
    config_path = os.path.join(project_dir, 'wrench_project.json')
    
    # Default configuration
    config = {
        'name': project_name,
        'version': '1.0.0',
        'template': template,
        'main_scene': 'main.wscene',
        'window': {
            'width': 1280,
            'height': 720,
            'title': project_name,
            'fullscreen': False,
            'vsync': True
        },
        'graphics': {
            'render_scale': 1.0,
            'shadow_quality': 'medium',
            'texture_quality': 'high',
            'max_fps': 60
        },
        'physics': {
            'gravity': [0, -9.81, 0],
            'solver_iterations': 10,
            'enable_sleeping': True
        }
    }
    
    # Load existing config if it exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_config = json.load(f)
            # Merge with default config
            config.update(existing_config)
    
    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a new Wrench project')
    parser.add_argument('name', help='Name of the project')
    parser.add_argument('--template', default='basic', help='Template to use (default: basic)')
    
    args = parser.parse_args()
    create_project(args.name, args.template)
