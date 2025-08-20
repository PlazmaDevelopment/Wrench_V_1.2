"""
Wrench Engine Fixes and Optimizations

This module contains various fixes and optimizations for the Wrench Engine.
"""

__all__ = ['apply_fixes', 'optimize_performance', 'check_system_requirements']

def apply_fixes():
    """Apply all available fixes to the Wrench Engine installation."""
    from . import performance, compatibility, graphics
    
    # Apply performance optimizations
    performance.optimize_rendering()
    performance.optimize_physics()
    
    # Apply compatibility fixes
    compatibility.fix_import_issues()
    compatibility.fix_path_issues()
    
    # Apply graphics optimizations
    graphics.optimize_shaders()
    graphics.adjust_graphics_settings()

def optimize_performance(profile='balanced'):
    """
    Optimize Wrench Engine performance based on the specified profile.
    
    Args:
        profile (str): Performance profile to use. Can be 'low', 'balanced', or 'high'.
    """
    from .performance import set_performance_profile
    set_performance_profile(profile)

def check_system_requirements():
    """Check if the system meets the minimum requirements for Wrench Engine."""
    from .compatibility import check_requirements
    return check_requirements()
