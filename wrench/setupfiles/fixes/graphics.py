"""
Graphics optimization module for Wrench Engine.

This module contains functions to optimize graphics settings and shaders.
"""

import os
import json
import platform
from typing import Dict, Any, Optional

def optimize_shaders() -> None:
    """Optimize shaders for the current hardware."""
    # Get the shader cache directory
    shader_cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'shaders')
    os.makedirs(shader_cache_dir, exist_ok=True)
    
    # Get system information
    system_info = get_graphics_info()
    
    # Optimize shader compilation based on GPU
    if 'NVIDIA' in system_info.get('gpu_vendor', ''):
        os.environ['__GL_THREADED_OPTIMIZATIONS'] = '1'
    elif 'AMD' in system_info.get('gpu_vendor', ''):
        os.environ['R600_ENABLE_SAMPLER_OPTIMIZATIONS'] = '1'
        os.environ['R600_DEBUG'] = 'nofmask'
    elif 'Intel' in system_info.get('gpu_vendor', ''):
        os.environ['INTEL_DEBUG'] = 'noforcemip'
