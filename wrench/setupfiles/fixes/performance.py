"""
Performance optimization module for Wrench Engine.

This module contains functions to optimize the performance of the Wrench Engine.
"""

import os
import json
import platform
import psutil
from typing import Dict, Any

def get_system_info() -> Dict[str, Any]:
    """
    Get system information including CPU, GPU, and memory.
    
    Returns:
        Dict containing system information.
    """
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_info = [{
            'name': gpu.name,
            'memory_total': gpu.memoryTotal,
            'memory_free': gpu.memoryFree,
            'memory_used': gpu.memoryUsed,
            'load': gpu.load * 100,
            'temperature': gpu.temperature
        } for gpu in gpus] if gpus else []
    except ImportError:
        gpu_info = []
    
    return {
        'system': {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'cpu_cores': psutil.cpu_count(logical=False),
            'cpu_threads': psutil.cpu_count(logical=True),
            'total_ram': psutil.virtual_memory().total / (1024 ** 3),  # in GB
        },
        'gpu': gpu_info
    }

def set_performance_profile(profile: str = 'balanced') -> None:
    """
    Set the performance profile for Wrench Engine.
    
    Args:
        profile: Performance profile ('low', 'balanced', or 'high').
    """
    profiles = {
        'low': {
            'render_quality': 0.75,
            'shadow_quality': 'low',
            'texture_quality': 'medium',
            'physics_quality': 'low',
            'max_fps': 30,
            'vsync': False,
            'particles': 'low',
            'post_processing': False
        },
        'balanced': {
            'render_quality': 1.0,
            'shadow_quality': 'medium',
            'texture_quality': 'high',
            'physics_quality': 'medium',
            'max_fps': 60,
            'vsync': True,
            'particles': 'medium',
            'post_processing': True
        },
        'high': {
            'render_quality': 1.5,
            'shadow_quality': 'high',
            'texture_quality': 'ultra',
            'physics_quality': 'high',
            'max_fps': 144,
            'vsync': True,
            'particles': 'high',
            'post_processing': True
        }
    }
    
    if profile not in profiles:
        raise ValueError(f"Invalid profile: {profile}. Must be one of: {list(profiles.keys())}")
    
    # Apply the selected profile
    config = load_config()
    config['graphics'].update(profiles[profile])
    save_config(config)

def optimize_rendering() -> None:
    """Optimize rendering settings based on system capabilities."""
    system_info = get_system_info()
    config = load_config()
    
    # Adjust settings based on GPU capabilities
    if system_info['gpu']:
        gpu = system_info['gpu'][0]  # Use first GPU
        
        # Adjust settings based on GPU memory
        if gpu['memory_total'] < 2000:  # Less than 2GB
            config['graphics']['texture_quality'] = 'low'
            config['graphics']['shadow_quality'] = 'low'
        elif gpu['memory_total'] < 4000:  # Less than 4GB
            config['graphics']['texture_quality'] = 'medium'
            config['graphics']['shadow_quality'] = 'medium'
        else:
            config['graphics']['texture_quality'] = 'high'
            config['graphics']['shadow_quality'] = 'high'
    
    # Adjust settings based on CPU capabilities
    if system_info['system']['cpu_cores'] < 4:
        config['physics']['threads'] = 1
        config['graphics']['particles'] = 'low'
    else:
        config['physics']['threads'] = min(4, system_info['system']['cpu_cores'] - 1)
    
    save_config(config)

def optimize_physics() -> None:
    """Optimize physics settings based on system capabilities."""
    system_info = get_system_info()
    config = load_config()
    
    # Adjust physics steps based on CPU capabilities
    if system_info['system']['cpu_cores'] < 4:
        config['physics']['max_steps_per_frame'] = 2
        config['physics']['solver_iterations'] = 8
    else:
        config['physics']['max_steps_per_frame'] = 4
        config['physics']['solver_iterations'] = 12
    
    save_config(config)

def load_config() -> Dict[str, Any]:
    """Load the Wrench Engine configuration."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'wrench_config.json')
    
    # Default configuration
    default_config = {
        'graphics': {
            'render_quality': 1.0,
            'shadow_quality': 'medium',
            'texture_quality': 'high',
            'vsync': True,
            'max_fps': 60,
            'particles': 'medium',
            'post_processing': True
        },
        'physics': {
            'threads': 2,
            'max_steps_per_frame': 4,
            'solver_iterations': 10,
            'gravity': [0, -9.81, 0]
        },
        'audio': {
            'volume': 1.0,
            'spatial_audio': True
        }
    }
    
    # Load config file if it exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with default config to ensure all keys exist
                return {**default_config, **config}
        except Exception as e:
            print(f"Error loading config: {e}")
    
    return default_config

def save_config(config: Dict[str, Any]) -> None:
    """Save the Wrench Engine configuration."""
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'wrench_config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def optimize_startup() -> None:
    """Optimize Wrench Engine startup performance."""
    # Enable Python optimizations
    import sys
    import warnings
    
    # Disable debug logging in production
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Optimize Python's import system
    sys.dont_write_bytecode = True
    
    # Disable debug checks in Python
    if hasattr(sys, 'setcheckinterval'):
        sys.setcheckinterval(100)  # For Python 2
    else:
        sys.setswitchinterval(0.005)  # For Python 3
    
    # Disable some Python warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    
    # Set environment variables for better performance
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    os.environ['PYGAME_BLEND_ALPHA_SDL2'] = '1'
