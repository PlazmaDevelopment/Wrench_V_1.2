"""
Advanced HDR rendering system with physically-based lighting, shadows, and atmospheric effects.
This module provides high-quality rendering features for realistic graphics.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import moderngl
import glm
import pygame
from pygame import gfxdraw
from enum import Enum, auto
import random
import math

# Constants
HDR_MAX_LUMINANCE = 10000.0  # Maximum HDR value (nits)
HDR_EXPOSURE = 1.0           # Default exposure
HDR_GAMMA = 2.2              # Gamma correction value

class LightType(Enum):
    """Types of light sources with physical properties."""
    DIRECTIONAL = auto()  # Sun/moon - infinite distance, parallel rays
    POINT = auto()        # Omnidirectional point light (light bulbs)
    SPOT = auto()         # Spotlight - directional with falloff
    AREA = auto()         # Area light - rectangle or disk shape
    SKY = auto()          # Environment/sky light
    MESH = auto()         # Mesh-based light source
    VOLUME = auto()       # Volumetric light (god rays, light shafts)
    IES = auto()          # IES profile-based light

@dataclass
class LightProfile:
    """IES light profile data for realistic light distribution."""
    name: str
    data: np.ndarray  # Photometric data
    horizontal_angles: np.ndarray
    vertical_angles: np.ndarray
    candela_values: np.ndarray
    
    @classmethod
    def from_ies_file(cls, filepath: str) -> 'LightProfile':
        """Load IES profile from .ies file."""
        # Parse IES file and extract photometric data
        # Implementation depends on IES file parser
        pass
    
    def to_texture(self, ctx) -> Any:
        """Convert IES profile to a 2D texture for GPU sampling."""
        # Convert photometric data to 2D texture
        pass

@dataclass
class Light:
    """Advanced light source with physical properties and IES profiles."""
    # Basic properties
    name: str = "Light"
    light_type: LightType = LightType.POINT
    enabled: bool = True
    visible: bool = True
    layer_mask: int = 0xFFFFFFFF  # Which layers this light affects
    
    # Color and intensity
    color: Tuple[float, float, float] = (1.0, 0.95, 0.9)  # Warm white by default
    temperature: float = 6500.0  # Color temperature in Kelvin
    intensity: float = 1000.0    # In lumens (for point/spot) or lux (for directional)
    
    # Position and orientation
    position: Tuple[float, float, float] = (0, 10, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)
    direction: Tuple[float, float, float] = (0, -1, 0)  # For directional/spot lights
    
    # Attenuation (for point/spot lights)
    range: float = 10.0  # Maximum range in meters
    attenuation: Tuple[float, float, float] = (1.0, 0.09, 0.032)  # Constant, Linear, Quadratic
    
    # Spotlight properties
    inner_angle: float = 30.0  # In degrees
    outer_angle: float = 45.0  # In degrees
    falloff: float = 1.0       # Falloff exponent
    
    # Area light properties
    area_size: Tuple[float, float] = (1.0, 1.0)  # Width and height in meters
    area_shape: str = 'rect'   # 'rect' or 'disk'
    
    # IES profile
    ies_profile: Optional[LightProfile] = None
    ies_intensity: float = 1.0
    ies_texture: Optional[Any] = None
    
    # Shadows
    casts_shadows: bool = True
    shadow_map_size: int = 4096  # Higher resolution for better quality
    shadow_bias: float = 0.001
    shadow_normal_bias: float = 0.05
    shadow_softness: float = 0.5  # PCSS soft shadows
    shadow_samples: int = 16      # Number of samples for soft shadows
    
    # Volumetric lighting
    volumetric: bool = True
    volumetric_intensity: float = 1.0
    volumetric_steps: int = 64
    volumetric_scattering: float = 0.5
    
    # Indirect lighting
    bounce_light: bool = True
    bounce_intensity: float = 0.3
    
    # Lens effects
    lens_flare: bool = False
    lens_flare_texture: Optional[Any] = None
    lens_flare_elements: List[Dict] = field(default_factory=list)
    
    # Runtime data
    _shadow_map: Optional[Any] = None
    _shadow_fbo: Optional[Any] = None
    _view_matrix: np.ndarray = field(init=False)
    _projection_matrix: np.ndarray = field(init=False)
    _frustum: Optional[Any] = None
    
    def __post_init__(self):
        self._update_matrices()
    
    def _update_matrices(self) -> None:
        """Update light view and projection matrices."""
        if self.light_type == LightType.DIRECTIONAL:
            # Orthographic projection for directional lights
            self._view_matrix = self._get_directional_view_matrix()
            self._projection_matrix = self._get_ortho_projection()
        elif self.light_type in (LightType.POINT, LightType.SPOT):
            # Perspective projection for point/spot lights
            self._view_matrix = self._get_point_view_matrix()
            self._projection_matrix = self._get_perspective_projection()
        
        # Update frustum for culling
        self._update_frustum()
    
    def _get_directional_view_matrix(self) -> np.ndarray:
        """Get view matrix for directional light."""
        return glm.lookAt(
            np.array(self.position, dtype=np.float32),
            np.array(self.position, dtype=np.float32) + np.array(self.direction, dtype=np.float32),
            np.array([0, 1, 0], dtype=np.float32)
        )
    
    def _get_point_view_matrix(self) -> np.ndarray:
        """Get view matrix for point/spot light."""
        return glm.lookAt(
            np.array(self.position, dtype=np.float32),
            np.array(self.position, dtype=np.float32) + np.array(self.direction, dtype=np.float32),
            np.array([0, 1, 0], dtype=np.float32)  # Up vector
        )
    
    def _get_ortho_projection(self, cascade_index: int = 0, num_cascades: int = 1) -> np.ndarray:
        """Get orthographic projection for directional light with CSM support."""
        # Implementation for cascaded shadow maps
        # This is a simplified version - actual implementation would use scene bounds
        return glm.ortho(-10, 10, -10, 10, 0.1, 100.0)
    
    def _get_perspective_projection(self) -> np.ndarray:
        """Get perspective projection for point/spot light."""
        if self.light_type == LightType.SPOT:
            return glm.perspective(
                glm.radians(self.outer_angle * 2),  # FOV
                1.0,  # Aspect ratio
                0.1,  # Near plane
                self.range  # Far plane
            )
        else:  # Point light
            return glm.perspective(
                glm.radians(90),  # 90° for each face of the cubemap
                1.0,  # Aspect ratio
                0.1,  # Near plane
                self.range  # Far plane
            )
    
    def _update_frustum(self) -> None:
        """Update frustum planes for culling."""
        # Implementation of frustum plane extraction
        pass
    
    def get_shadow_map(self, ctx, index: int = 0) -> Any:
        """Get or create shadow map texture."""
        if self._shadow_map is None:
            if self.light_type == LightType.POINT:
                # Cube map for point light shadows
                self._shadow_map = ctx.texture_cube(
                    (self.shadow_map_size, self.shadow_map_size),
                    1,  # 1 channel (depth)
                    dtype='f4'
                )
            else:
                # 2D texture for directional/spot lights
                self._shadow_map = ctx.depth_texture(
                    (self.shadow_map_size, self.shadow_map_size)
                )
                self._shadow_fbo = ctx.framebuffer(depth_attachment=self._shadow_map)
        
        return self._shadow_map, self._shadow_fbo
    
    def get_light_data(self) -> Dict:
        """Get light data for shader uniforms."""
        return {
            'type': self.light_type.value,
            'position': (*self.position, 1.0 if self.light_type != LightType.DIRECTIONAL else 0.0),
            'direction': (*self.direction, 0.0),
            'color': (*self.color, 1.0),
            'intensity': self.intensity,
            'range': self.range,
            'inner_angle': math.cos(math.radians(self.inner_angle * 0.5)),
            'outer_angle': math.cos(math.radians(self.outer_angle * 0.5)),
            'attenuation': self.attenuation,
            'shadow_map_index': 0,  # Will be set by renderer
            'shadow_bias': self.shadow_bias,
            'shadow_normal_bias': self.shadow_normal_bias,
            'shadow_softness': self.shadow_softness,
            'volumetric': 1.0 if self.volumetric else 0.0,
            'volumetric_intensity': self.volumetric_intensity,
            'area_size': (*self.area_size, 0.0, 0.0) if self.light_type == LightType.AREA else (0.0, 0.0, 0.0, 0.0),
            'ies_texture_index': -1  # Will be set if IES profile is used
        }

@dataclass
class MaterialType(Enum):
    """Types of materials with different shading models."""
    STANDARD = auto()       # Standard PBR material
    SUBSURFACE = auto()     # For skin, wax, marble
    CLOTH = auto()          # Fabric and cloth materials
    CLEARCOAT = auto()      # For car paint, plastics
    GLASS = auto()          # Transparent materials
    EMISSIVE = auto()       # Self-illuminated materials
    FOLIAGE = auto()        # For vegetation
    SKIN = auto()           # For character skin
    HAIR = auto()           # For hair/fur rendering
    EYE = auto()            # Specialized for eyes
    
@dataclass
class Material:
    """Advanced physically-based material with support for various material types."""
    # Basic identification
    name: str = "DefaultMaterial"
    material_type: MaterialType = MaterialType.STANDARD
    two_sided: bool = False
    alpha_mode: str = 'OPAQUE'  # OPAQUE, MASK, BLEND
    alpha_cutoff: float = 0.5
    
    # Base properties
    albedo: Tuple[float, float, float] = (0.8, 0.8, 0.8)
    metallic: float = 0.0
    roughness: float = 0.5
    ao: float = 1.0
    emission: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    emission_strength: float = 1.0
    
    # Textures (stored as OpenGL texture IDs after loading)
    albedo_map: Optional[int] = None
    normal_map: Optional[int] = None
    metallic_map: Optional[int] = None
    roughness_map: Optional[int] = None
    ao_map: Optional[int] = None
    emission_map: Optional[int] = None
    height_map: Optional[int] = None
    
    # Advanced material properties
    # Subsurface scattering
    subsurface: float = 0.0
    subsurface_color: Tuple[float, float, float] = (1.0, 0.1, 0.1)
    subsurface_radius: Tuple[float, float, float] = (1.0, 0.2, 0.1)
    subsurface_ior: float = 1.4
    subsurface_anisotropy: float = 0.0
    
    # Clearcoat (for car paint, plastics)
    clearcoat: float = 0.0
    clearcoat_roughness: float = 0.03
    clearcoat_normal_map: Optional[int] = None
    
    # Sheen (for cloth materials)
    sheen: float = 0.0
    sheen_tint: float = 0.5
    sheen_roughness: float = 0.3
    
    # Anisotropy (for brushed metals, CD surfaces)
    anisotropic: float = 0.0
    anisotropic_rotation: float = 0.0
    anisotropic_map: Optional[int] = None
    
    # Transmission (for glass, liquids)
    transmission: float = 0.0
    ior: float = 1.45  # Index of refraction
    thickness: float = 0.01
    thickness_map: Optional[int] = None
    
    # Displacement
    displacement_strength: float = 0.1
    displacement_midlevel: float = 0.5
    
    # Detail maps
    detail_albedo_map: Optional[int] = None
    detail_normal_map: Optional[int] = None
    detail_roughness_map: Optional[int] = None
    detail_scale: float = 1.0
    
    # UV mapping
    uv_scale: Tuple[float, float] = (1.0, 1.0)
    uv_offset: Tuple[float, float] = (0.0, 0.0)
    
    # Tessellation
    tessellation_factor: float = 1.0
    
    # Physics properties
    density: float = 1.0  # g/cm³
    friction: float = 0.5
    restitution: float = 0.2
    
    # Custom shader parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime data (not serialized)
    _shader_program: Optional[Any] = None
    _uniform_cache: Dict[str, Any] = field(default_factory=dict)
    
    def get_shader_defines(self) -> Dict[str, str]:
        """Get shader preprocessor defines based on material properties."""
        defines = {
            'MATERIAL_TYPE': str(self.material_type.value),
            'HAS_ALBEDO_MAP': '1' if self.albedo_map else '0',
            'HAS_NORMAL_MAP': '1' if self.normal_map else '0',
            'HAS_METALLIC_MAP': '1' if self.metallic_map else '0',
            'HAS_ROUGHNESS_MAP': '1' if self.roughness_map else '0',
            'HAS_AO_MAP': '1' if self.ao_map else '0',
            'HAS_EMISSION_MAP': '1' if self.emission_map else '0',
            'HAS_HEIGHT_MAP': '1' if self.height_map else '0',
            'HAS_CLEARCOAT_NORMAL_MAP': '1' if self.clearcoat_normal_map else '0',
            'HAS_ANISOTROPY_MAP': '1' if self.anisotropic_map else '0',
            'HAS_THICKNESS_MAP': '1' if self.thickness_map else '0',
            'HAS_DETAIL_ALBEDO_MAP': '1' if self.detail_albedo_map else '0',
            'HAS_DETAIL_NORMAL_MAP': '1' if self.detail_normal_map else '0',
            'HAS_DETAIL_ROUGHNESS_MAP': '1' if self.detail_roughness_map else '0',
            'TWO_SIDED': '1' if self.two_sided else '0',
            'ALPHA_MODE': f'ALPHA_MODE_{self.alpha_mode}'
        }
        return defines
    
    def bind_textures(self, ctx) -> None:
        """Bind all material textures to their respective texture units."""
        texture_units = {
            0: self.albedo_map,
            1: self.normal_map,
            2: self.metallic_map,
            3: self.roughness_map,
            4: self.ao_map,
            5: self.emission_map,
            6: self.height_map,
            7: self.clearcoat_normal_map,
            8: self.anisotropic_map,
            9: self.thickness_map,
            10: self.detail_albedo_map,
            11: self.detail_normal_map,
            12: self.detail_roughness_map
        }
        
        for unit, tex_id in texture_units.items():
            if tex_id is not None:
                ctx.texture = (unit, tex_id)
    
    def update_uniforms(self, shader_program) -> None:
        """Update shader uniforms with material properties."""
        # Basic properties
        shader_program['u_Material.albedo'] = self.albedo
        shader_program['u_Material.metallic'] = self.metallic
        shader_program['u_Material.roughness'] = self.roughness
        shader_program['u_Material.ao'] = self.ao
        shader_program['u_Material.emission'] = self.emission
        shader_program['u_Material.emission_strength'] = self.emission_strength
        
        # Subsurface scattering
        shader_program['u_Material.subsurface'] = self.subsurface
        shader_program['u_Material.subsurface_color'] = self.subsurface_color
        shader_program['u_Material.subsurface_radius'] = self.subsurface_radius
        shader_program['u_Material.subsurface_ior'] = self.subsurface_ior
        shader_program['u_Material.subsurface_anisotropy'] = self.subsurface_anisotropy
        
        # Clearcoat
        shader_program['u_Material.clearcoat'] = self.clearcoat
        shader_program['u_Material.clearcoat_roughness'] = self.clearcoat_roughness
        
        # Sheen
        shader_program['u_Material.sheen'] = self.sheen
        shader_program['u_Material.sheen_tint'] = self.sheen_tint
        shader_program['u_Material.sheen_roughness'] = self.sheen_roughness
        
        # Anisotropy
        shader_program['u_Material.anisotropic'] = self.anisotropic
        shader_program['u_Material.anisotropic_rotation'] = self.anisotropic_rotation
        
        # Transmission
        shader_program['u_Material.transmission'] = self.transmission
        shader_program['u_Material.ior'] = self.ior
        shader_program['u_Material.thickness'] = self.thickness
        
        # Displacement
        shader_program['u_Material.displacement_strength'] = self.displacement_strength
        shader_program['u_Material.displacement_midlevel'] = self.displacement_midlevel
        
        # Detail maps
        shader_program['u_Material.detail_scale'] = self.detail_scale
        
        # UV mapping
        shader_program['u_Material.uv_scale'] = self.uv_scale
        shader_program['u_Material.uv_offset'] = self.uv_offset
        
        # Alpha mode
        shader_program['u_Material.alpha_cutoff'] = self.alpha_cutoff

class AtmosphereSettings:
    """Atmospheric and weather simulation settings."""
    
    def __init__(self):
        # Sun properties
        self.sun_direction = glm.normalize(glm.vec3(0.5, 1.0, 0.5))
        self.sun_intensity = 1.0
        self.sun_angular_radius = 0.00935  # ~0.53 degrees
        self.sun_color = glm.vec3(1.0, 1.0, 1.0)
        
        # Atmosphere properties
        self.rayleigh_scattering = glm.vec3(5.8e-6, 13.5e-6, 33.1e-6)  # Rayleigh scattering coefficients
        self.mie_scattering = glm.vec3(21e-6)  # Mie scattering coefficients
        self.rayleigh_scale_height = 8.0e3  # Scale height for Rayleigh scattering (meters)
        self.mie_scale_height = 1.2e3      # Scale height for Mie scattering (meters)
        self.mie_direction = 0.76          # Mie preferred scattering direction (0.0 to 1.0)
        
        # Planet properties
        self.planet_radius = 6.371e6       # Earth radius in meters
        self.atmosphere_radius = 6.471e6   # Top of atmosphere in meters
        
        # Aerial perspective
        self.aerial_perspective = True
        self.aerial_perspective_steps = 16
        
        # Fog
        self.fog_density = 0.01
        self.fog_color = glm.vec3(0.7, 0.8, 1.0)
        self.fog_height_falloff = 0.2
        
        # Weather
        self.weather = {
            'clouds': {
                'enabled': True,
                'coverage': 0.3,  # 0-1 cloud coverage
                'density': 0.5,   # 0-1 cloud density
                'wind_speed': 10.0,  # m/s
                'wind_direction': glm.vec2(1.0, 0.0),
                'precipitation': 0.0,  # 0-1 precipitation amount
                'light_absorption': 0.05,  # How much light clouds absorb
                'scattering_strength': 0.5,  # Light scattering in clouds
                'ambient_occlusion': 0.2,  # Self-shadowing in clouds
                'detail_strength': 0.3,    # Detail noise strength
                'curl_strength': 0.5,      # Curl noise for realistic shapes
            },
            'rain': {
                'enabled': False,
                'intensity': 0.0,  # 0-1
                'speed': 5.0,      # Falling speed
                'wind_influence': 0.2,  # How much wind affects rain
                'splash_size': 0.1,    # Size of rain splashes
                'splash_lifetime': 1.0,  # How long splashes last (seconds)
            },
            'snow': {
                'enabled': False,
                'intensity': 0.0,  # 0-1
                'size': 0.05,      # Flake size
                'speed': 1.0,      # Falling speed
                'wind_influence': 0.1,  # How much wind affects snow
                'accumulation': 0.0,  # Ground accumulation amount
            },
            'fog': {
                'enabled': True,
                'density': 0.01,
                'color': glm.vec3(0.7, 0.8, 1.0),
                'height_falloff': 0.2,
                'height': 0.0,  # Base height of the fog
            },
            'wind': {
                'speed': 5.0,  # m/s
                'direction': glm.vec2(1.0, 0.0),  # Normalized direction
                'turbulence': 0.2,  # Wind turbulence amount
            }
        }
        
        # Time of day (0-24 hours)
        self.time_of_day = 12.0
        self.time_scale = 1.0  # Speed of time (1.0 = real-time)
        
        # Sky state
        self.cloud_speed = 0.1
        self.cloud_scale = 0.0001
        self.star_intensity = 1.0
        self.moon_intensity = 0.1
        
        # Precomputed values
        self._sun_zenith_angle = 0.0
        self._sun_azimuth = 0.0
        self._moon_direction = glm.vec3(0.0)
        self._update_sun_position()
    
    def _update_sun_position(self) -> None:
        """Update sun position based on time of day."""
        # Convert time of day to angle (0-2π)
        time_angle = (self.time_of_day / 24.0) * math.pi * 2.0
        
        # Calculate sun direction (y-up coordinate system)
        self._sun_zenith_angle = math.cos(time_angle)
        self._sun_azimuth = math.sin(time_angle) * 0.5  # Slight offset for more interesting lighting
        
        # Update sun direction
        self.sun_direction = glm.normalize(glm.vec3(
            math.sin(self._sun_azimuth) * math.cos(self._sun_zenith_angle),
            math.sin(self._sun_zenith_angle),
            math.cos(self._sun_azimuth) * math.cos(self._sun_zenith_angle)
        ))
        
        # Update moon position (opposite to sun)
        self._moon_direction = -self.sun_direction
        
        # Update sun color based on angle (sunset/sunrise)
        sun_angle = max(0.0, self.sun_direction.y)
        self.sun_color = glm.mix(
            glm.vec3(1.0, 0.6, 0.4),  # Warm colors at sunrise/sunset
            glm.vec3(1.0, 1.0, 1.0),  # White at noon
            min(1.0, sun_angle * 2.0)
        )
        
        # Adjust intensity based on sun angle
        self.sun_intensity = max(0.0, self.sun_direction.y * 1.5 + 0.2)
    
    def update(self, delta_time: float) -> None:
        """Update atmospheric conditions based on time and weather."""
        # Update time
        self.time_of_day += delta_time * self.time_scale / 3600.0  # Convert to hours
        if self.time_of_day >= 24.0:
            self.time_of_day -= 24.0
        
        # Update sun position
        self._update_sun_position()
        
        # Update cloud movement
        cloud_wind = self.weather['wind']['direction'] * self.weather['wind']['speed'] * 0.01
        self.weather['clouds']['wind_direction'] += cloud_wind * delta_time
        
        # Update rain/snow based on cloud coverage
        if self.weather['clouds']['precipitation'] > 0.5:
            if not self.weather['rain']['enabled'] and not self.weather['snow']['enabled']:
                # Randomly choose between rain and snow based on temperature (simplified)
                is_snow = random.random() > 0.7  # 30% chance of snow
                if is_snow:
                    self.weather['snow']['enabled'] = True
                    self.weather['snow']['intensity'] = self.weather['clouds']['precipitation']
                else:
                    self.weather['rain']['enabled'] = True
                    self.weather['rain']['intensity'] = self.weather['clouds']['precipitation']
        else:
            self.weather['rain']['enabled'] = False
            self.weather['snow']['enabled'] = False
    
    def get_atmosphere_uniforms(self) -> Dict[str, Any]:
        """Get shader uniforms for atmospheric effects."""
        return {
            'u_Atmosphere.rayleigh_scattering': tuple(self.rayleigh_scattering),
            'u_Atmosphere.mie_scattering': tuple(self.mie_scattering),
            'u_Atmosphere.rayleigh_scale_height': self.rayleigh_scale_height,
            'u_Atmosphere.mie_scale_height': self.mie_scale_height,
            'u_Atmosphere.mie_direction': self.mie_direction,
            'u_Atmosphere.planet_radius': self.planet_radius,
            'u_Atmosphere.atmosphere_radius': self.atmosphere_radius,
            'u_Atmosphere.sun_direction': tuple(self.sun_direction),
            'u_Atmosphere.sun_intensity': self.sun_intensity,
            'u_Atmosphere.sun_color': tuple(self.sun_color),
            'u_Atmosphere.moon_direction': tuple(self._moon_direction),
            'u_Atmosphere.moon_intensity': self.moon_intensity,
            'u_Atmosphere.fog_density': self.fog_density,
            'u_Atmosphere.fog_color': tuple(self.fog_color),
            'u_Atmosphere.fog_height_falloff': self.fog_height_falloff,
            'u_Atmosphere.time': self.time_of_day,
            'u_Atmosphere.cloud_coverage': self.weather['clouds']['coverage'],
            'u_Atmosphere.cloud_density': self.weather['clouds']['density'],
            'u_Atmosphere.wind_direction': tuple(self.weather['wind']['direction']),
            'u_Atmosphere.wind_speed': self.weather['wind']['speed'],
            'u_Atmosphere.rain_intensity': self.weather['rain']['intensity'] if self.weather['rain']['enabled'] else 0.0,
            'u_Atmosphere.snow_intensity': self.weather['snow']['intensity'] if self.weather['snow']['enabled'] else 0.0,
        }

class PostProcessor:
    """Handles post-processing effects for HDR rendering."""
    
    class EffectType(Enum):
        TONE_MAPPING = auto()
        BLOOM = auto()
        SS_REFLECTIONS = auto()  # Screen-space reflections
        SS_GI = auto()          # Screen-space global illumination
        SSR = auto()            # Screen-space ray-traced reflections
        SSAO = auto()           # Screen-space ambient occlusion
        DOF = auto()            # Depth of field
        MOTION_BLUR = auto()
        CHROMATIC_ABERRATION = auto()
        VIGNETTE = auto()
        FILM_GRAIN = auto()
        LENS_FLARES = auto()
        COLOR_GRADING = auto()
        FXAA = auto()           # Fast Approximate Anti-Aliasing
        TAA = auto()           # Temporal Anti-Aliasing
        SHARPEN = auto()
        
    def __init__(self, width: int, height: int, hdr_enabled: bool = True):
        """Initialize the post-processor.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            hdr_enabled: Whether to use HDR rendering
        """
        self.width = width
        self.height = height
        self.hdr_enabled = hdr_enabled
        self.effects_enabled = {
            'tone_mapping': True,
            'bloom': True,
            'ssr': True,
            'ssao': True,
            'dof': False,
            'motion_blur': False,
            'chromatic_aberration': False,
            'vignette': True,
            'film_grain': False,
            'lens_flares': True,
            'color_grading': True,
            'fxaa': True,
            'taa': False,
            'sharpen': True,
        }
        
        # Effect parameters
        self.params = {
            'exposure': 1.0,  # Camera exposure (stops)
            'white_point': 1.0,  # White point for tone mapping
            'bloom_threshold': 1.0,  # Brightness threshold for bloom
            'bloom_intensity': 0.04,  # Bloom effect intensity
            'bloom_radius': 0.6,  # Bloom effect radius
            'bloom_knee': 0.1,  # Bloom soft threshold knee
            'ssr_intensity': 0.8,  # Screen-space reflections intensity
            'ssr_ray_step': 0.1,  # Ray step size for SSR
            'ssr_max_steps': 32,  # Maximum ray steps for SSR
            'ssr_binary_search_steps': 8,  # Binary search steps for SSR
            'ssr_thickness': 0.1,  # Thickness for depth testing in SSR
            'ssao_radius': 0.5,  # SSAO effect radius
            'ssao_bias': 0.025,  # SSAO depth bias
            'ssao_power': 2.0,  # SSAO power
            'dof_focus_distance': 10.0,  # Depth of field focus distance
            'dof_aperture': 1.0,  # Depth of field aperture (f-stop)
            'dof_focal_length': 0.05,  # Depth of field focal length
            'motion_blur_intensity': 0.5,  # Motion blur intensity
            'chromatic_aberration_intensity': 0.0,  # Chromatic aberration intensity
            'vignette_intensity': 0.3,  # Vignette intensity
            'vignette_softness': 0.4,  # Vignette softness
            'film_grain_intensity': 0.05,  # Film grain intensity
            'sharpen_strength': 0.5,  # Sharpening strength
            'contrast': 1.0,  # Color grading contrast
            'saturation': 1.0,  # Color grading saturation
            'brightness': 1.0,  # Color grading brightness
            'temperature': 0.0,  # Color temperature (-1.0 to 1.0)
            'tint': 0.0,  # Color tint (-1.0 to 1.0)
        }
        
        # Initialize shaders and framebuffers
        self._init_resources()
    
    def _init_resources(self) -> None:
        """Initialize OpenGL resources for post-processing."""
        # Create HDR framebuffer
        self.hdr_fbo = self._create_hdr_framebuffer()
        
        # Create ping-pong framebuffers for bloom
        self.pingpong_fbos = [
            self._create_pingpong_framebuffer(),
            self._create_pingpong_framebuffer()
        ]
        
        # Create SSAO framebuffer
        self.ssao_fbo = self._create_ssao_framebuffer()
        
        # Load shaders
        self._load_shaders()
        
        # Generate SSAO noise texture
        self._generate_ssao_noise()
    
    def _create_hdr_framebuffer(self) -> Any:
        """Create HDR framebuffer with color and depth attachments."""
        # Implementation depends on your rendering backend (ModernGL, PyOpenGL, etc.)
        pass
    
    def _create_pingpong_framebuffer(self) -> Any:
        """Create a ping-pong framebuffer for bloom and other effects."""
        pass
    
    def _create_ssao_framebuffer(self) -> Any:
        """Create framebuffer for SSAO."""
        pass
    
    def _load_shaders(self) -> None:
        """Load all post-processing shaders."""
        # Implementation depends on your shader loading system
        pass
    
    def _generate_ssao_noise(self) -> None:
        """Generate noise texture for SSAO."""
        # Generate random rotation vectors
        noise = np.random.rand(4, 4, 3).astype(np.float32) * 2.0 - 1.0
        # Normalize to get vectors on a sphere
        noise = noise / np.linalg.norm(noise, axis=2, keepdims=True)
        # Create texture
        # Implementation depends on your rendering backend
        pass
    
    def apply_effects(self, scene_texture: Any, depth_texture: Any, 
                     velocity_texture: Any, camera: Any) -> Any:
        """Apply post-processing effects to the rendered scene.
        
        Args:
            scene_texture: The rendered scene texture (HDR)
            depth_texture: Depth buffer
            velocity_texture: Motion vectors for motion blur and TAA
            camera: Camera information
            
        Returns:
            Processed final image
        """
        # Start with the original HDR scene
        current_target = scene_texture
        
        # Apply SSAO if enabled
        if self.effects_enabled['ssao']:
            current_target = self._apply_ssao(current_target, depth_texture, camera)
        
        # Apply SSR if enabled
        if self.effects_enabled['ssr']:
            current_target = self._apply_ssr(current_target, depth_texture, camera)
        
        # Apply bloom if enabled
        if self.effects_enabled['bloom']:
            current_target = self._apply_bloom(current_target)
        
        # Apply depth of field if enabled
        if self.effects_enabled['dof']:
            current_target = self._apply_dof(current_target, depth_texture, camera)
        
        # Apply motion blur if enabled
        if self.effects_enabled['motion_blur'] and velocity_texture is not None:
            current_target = self._apply_motion_blur(current_target, velocity_texture)
        
        # Apply lens flares if enabled
        if self.effects_enabled['lens_flares']:
            current_target = self._apply_lens_flares(current_target, depth_texture, camera)
        
        # Apply color grading and tone mapping
        current_target = self._apply_color_grading(current_target)
        
        # Apply film grain if enabled
        if self.effects_enabled['film_grain']:
            current_target = self._apply_film_grain(current_target)
        
        # Apply vignette if enabled
        if self.effects_enabled['vignette']:
            current_target = self._apply_vignette(current_target)
        
        # Apply chromatic aberration if enabled
        if self.effects_enabled['chromatic_aberration']:
            current_target = self._apply_chromatic_aberration(current_target)
        
        # Apply sharpening if enabled
        if self.effects_enabled['sharpen']:
            current_target = self._apply_sharpen(current_target)
        
        # Apply anti-aliasing
        if self.effects_enabled['taa']:
            current_target = self._apply_taa(current_target, velocity_texture)
        elif self.effects_enabled['fxaa']:
            current_target = self._apply_fxaa(current_target)
        
        return current_target
    
    def _apply_bloom(self, source_texture: Any) -> Any:
        """Apply bloom effect to the source texture."""
        # Extract bright areas
        threshold = self.params['bloom_threshold']
        bright_pixels = self._extract_bright_pixels(source_texture, threshold)
        
        # Blur the bright areas
        blurred = self._blur_texture(bright_pixels, self.params['bloom_radius'])
        
        # Blend with original
        return self._blend_textures(source_texture, blurred, self.params['bloom_intensity'])
    
    def _apply_ssao(self, source_texture: Any, depth_texture: Any, camera: Any) -> Any:
        """Apply screen-space ambient occlusion."""
        # Implementation of SSAO
        pass
    
    def _apply_ssr(self, source_texture: Any, depth_texture: Any, camera: Any) -> Any:
        """Apply screen-space reflections."""
        # Implementation of SSR
        pass
    
    def _apply_dof(self, source_texture: Any, depth_texture: Any, camera: Any) -> Any:
        """Apply depth of field effect."""
        # Implementation of depth of field
        pass
    
    def _apply_motion_blur(self, source_texture: Any, velocity_texture: Any) -> Any:
        """Apply motion blur based on velocity buffer."""
        # Implementation of motion blur
        pass
    
    def _apply_lens_flares(self, source_texture: Any, depth_texture: Any, camera: Any) -> Any:
        """Apply lens flare effects from bright light sources."""
        # Implementation of lens flares
        pass
    
    def _apply_color_grading(self, source_texture: Any) -> Any:
        """Apply color grading and tone mapping."""
        # Implementation of color grading and tone mapping
        pass
    
    def _apply_film_grain(self, source_texture: Any) -> Any:
        """Apply film grain effect."""
        # Implementation of film grain
        pass
    
    def _apply_vignette(self, source_texture: Any) -> Any:
        """Apply vignette effect."""
        # Implementation of vignette
        pass
    
    def _apply_chromatic_aberration(self, source_texture: Any) -> Any:
        """Apply chromatic aberration effect."""
        # Implementation of chromatic aberration
        pass
    
    def _apply_sharpen(self, source_texture: Any) -> Any:
        """Apply sharpening effect."""
        # Implementation of sharpening
        pass
    
    def _apply_fxaa(self, source_texture: Any) -> Any:
        """Apply FXAA (Fast Approximate Anti-Aliasing)."""
        # Implementation of FXAA
        pass
    
    def _apply_taa(self, source_texture: Any, velocity_texture: Any) -> Any:
        """Apply TAA (Temporal Anti-Aliasing)."""
        # Implementation of TAA
        pass

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import glm
import os
from typing import Dict, Any, Optional, List, Tuple, Union

class ShaderProgram:
    """Helper class for managing OpenGL shader programs."""
    
    def __init__(self, vertex_shader: str, fragment_shader: str, geometry_shader: str = None):
        """Compile and link shader program.
        
        Args:
            vertex_shader: Vertex shader source code
            fragment_shader: Fragment shader source code
            geometry_shader: Optional geometry shader source code
        """
        self.program = glCreateProgram()
        
        # Compile shaders
        vertex = self._compile_shader(vertex_shader, GL_VERTEX_SHADER)
        fragment = self._compile_shader(fragment_shader, GL_FRAGMENT_SHADER)
        geometry = None
        
        if geometry_shader:
            geometry = self._compile_shader(geometry_shader, GL_GEOMETRY_SHADER)
        
        # Attach shaders
        glAttachShader(self.program, vertex)
        glAttachShader(self.program, fragment)
        if geometry:
            glAttachShader(self.program, geometry)
        
        # Link program
        glLinkProgram(self.program)
        
        # Check for linking errors
        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            info = glGetProgramInfoLog(self.program)
            glDeleteProgram(self.program)
            raise RuntimeError(f"Shader program linking error: {info}")
        
        # Clean up shaders
        glDeleteShader(vertex)
        glDeleteShader(fragment)
        if geometry:
            glDeleteShader(geometry)
    
    def _compile_shader(self, source: str, shader_type: int) -> int:
        """Compile a shader from source."""
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            info = glGetShaderInfoLog(shader)
            glDeleteShader(shader)
            raise RuntimeError(f"Shader compilation error: {info}")
            
        return shader
    
    def use(self) -> None:
        """Use this shader program."""
        glUseProgram(self.program)
    
    def set_bool(self, name: str, value: bool) -> None:
        """Set a boolean uniform."""
        glUniform1i(glGetUniformLocation(self.program, name), int(value))
    
    def set_int(self, name: str, value: int) -> None:
        """Set an integer uniform."""
        glUniform1i(glGetUniformLocation(self.program, name), value)
    
    def set_float(self, name: str, value: float) -> None:
        """Set a float uniform."""
        glUniform1f(glGetUniformLocation(self.program, name), value)
    
    def set_vec2(self, name: str, value: Tuple[float, float]) -> None:
        """Set a 2D vector uniform."""
        glUniform2f(glGetUniformLocation(self.program, name), *value)
    
    def set_vec3(self, name: str, value: Tuple[float, float, float]) -> None:
        """Set a 3D vector uniform."""
        glUniform3f(glGetUniformLocation(self.program, name), *value)
    
    def set_vec4(self, name: str, value: Tuple[float, float, float, float]) -> None:
        """Set a 4D vector uniform."""
        glUniform4f(glGetUniformLocation(self.program, name), *value)
    
    def set_mat2(self, name: str, value: np.ndarray) -> None:
        """Set a 2x2 matrix uniform."""
        glUniformMatrix2fv(glGetUniformLocation(self.program, name), 1, GL_FALSE, value)
    
    def set_mat3(self, name: str, value: np.ndarray) -> None:
        """Set a 3x3 matrix uniform."""
        glUniformMatrix3fv(glGetUniformLocation(self.program, name), 1, GL_FALSE, value)
    
    def set_mat4(self, name: str, value: np.ndarray) -> None:
        """Set a 4x4 matrix uniform."""
        glUniformMatrix4fv(glGetUniformLocation(self.program, name), 1, GL_FALSE, value)
    
    def delete(self) -> None:
        """Delete the shader program."""
        glDeleteProgram(self.program)


class HDRRenderer:
    """Advanced HDR rendering system with PBR, atmospheric effects, and post-processing.
    
    This class serves as the main entry point for the HDR rendering pipeline, integrating
    materials, lighting, atmospheric effects, and post-processing into a cohesive system.
    """
    
    def __init__(self, width: int, height: int, hdr_enabled: bool = True):
        """Initialize the HDR renderer.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            hdr_enabled: Whether to use HDR rendering (default: True)
        """
        # Store configuration
        self.width = width
        self.height = height
        self.hdr_enabled = hdr_enabled
        self.frame_count = 0
        self.time = 0.0
        
        # Initialize OpenGL
        self._init_opengl()
        
        # Load shaders
        self.shaders = self._load_shaders()
        
        # Initialize framebuffers
        self._init_framebuffers()
        
        # Initialize render passes
        self._init_render_passes()
        
        # Initialize default resources
        self._init_default_resources()
        
        # Initialize statistics
        self.stats = {
            'draw_calls': 0,
            'triangles': 0,
            'lights': 0,
            'materials': 0,
            'meshes': 0,
            'fps': 0.0,
            'frame_time': 0.0,
        }
        
        # Debug settings
        self.debug = {
            'show_wireframe': False,
            'show_bounds': False,
            'show_normals': False,
            'show_shadow_cascades': False,
            'show_ssao': False,
            'show_light_volumes': False,
        }
    
    def _load_shaders(self) -> Dict[str, ShaderProgram]:
        """Load and compile all shaders."""
        from . import shaders as shader_defs
        
        shader_programs = {}
        
        try:
            # PBR shader
            shader_programs['pbr'] = ShaderProgram(
                vertex_shader=shader_defs.PBR_VERTEX_SHADER,
                fragment_shader=shader_defs.PBR_FRAGMENT_SHADER
            )
            
            # Lighting shader
            shader_programs['lighting'] = ShaderProgram(
                vertex_shader=shader_defs.LIGHTING_VERTEX_SHADER,
                fragment_shader=shader_defs.LIGHTING_FRAGMENT_SHADER
            )
            
            # Skybox shader
            shader_programs['skybox'] = ShaderProgram(
                vertex_shader=shader_defs.SKYBOX_VERTEX_SHADER,
                fragment_shader=shader_defs.SKYBOX_FRAGMENT_SHADER
            )
            
            # Shadow map shader
            shader_programs['shadow_map'] = ShaderProgram(
                vertex_shader=shader_defs.SHADOW_MAP_VERTEX_SHADER,
                fragment_shader=shader_defs.SHADOW_MAP_FRAGMENT_SHADER
            )
            
            # Post-processing shaders
            shader_programs['post'] = ShaderProgram(
                vertex_shader=shader_defs.FULLSCREEN_QUAD_VERTEX_SHADER,
                fragment_shader=shader_defs.FULLSCREEN_QUAD_VERTEX_SHADER  # Dummy fragment shader
            )
            
            shader_programs['bloom'] = ShaderProgram(
                vertex_shader=shader_defs.FULLSCREEN_QUAD_VERTEX_SHADER,
                fragment_shader=shader_defs.BLOOM_FRAGMENT_SHADER
            )
            
            shader_programs['ssao'] = ShaderProgram(
                vertex_shader=shader_defs.FULLSCREEN_QUAD_VERTEX_SHADER,
                fragment_shader=shader_defs.SSAO_FRAGMENT_SHADER
            )
            
            shader_programs['tone_mapping'] = ShaderProgram(
                vertex_shader=shader_defs.FULLSCREEN_QUAD_VERTEX_SHADER,
                fragment_shader=shader_defs.TONE_MAPPING_FRAGMENT_SHADER
            )
            
            # Debug shaders
            shader_programs['debug'] = ShaderProgram(
                vertex_shader=shader_defs.DEBUG_VERTEX_SHADER,
                fragment_shader=shader_defs.DEBUG_FRAGMENT_SHADER
            )
            
            return shader_programs
            
        except Exception as e:
            # Clean up any partially created shaders
            for shader in shader_programs.values():
                shader.delete()
            raise RuntimeError(f"Failed to load shaders: {str(e)}")
    
    def _init_opengl(self) -> None:
        """Initialize OpenGL state and capabilities."""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable face culling
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        
        # Enable seamless cubemap filtering
        glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
        
        # Enable blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Set clear color and depth
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClearDepth(1.0)
    
    def _init_framebuffers(self) -> None:
        """Initialize framebuffers for deferred rendering and post-processing."""
        # G-buffer for deferred rendering
        self.g_buffer = self._create_gbuffer()
        
        # HDR framebuffer for lighting
        self.hdr_fbo = self._create_hdr_framebuffer()
        
        # Bloom framebuffers
        self.bloom_fbos = self._create_bloom_framebuffers()
        
        # SSAO framebuffer
        self.ssao_fbo = self._create_ssao_framebuffer()
    
    def _init_render_passes(self) -> None:
        """Initialize render passes for the rendering pipeline."""
        self.render_passes = {
            'geometry': self._render_geometry_pass,
            'lighting': self._render_lighting_pass,
            'ssao': self._render_ssao_pass,
            'skybox': self._render_skybox_pass,
            'post_processing': self._render_post_processing
        }
    
    def _init_default_resources(self) -> None:
        """Initialize default textures, materials, and other resources."""
        # Create default white texture
        self.default_texture = self._create_default_texture()
        
        # Create default material
        self.default_material = self._create_default_material()
        
        # Create fullscreen quad VAO
        self.quad_vao = self._create_quad_vao()
        
        # Create cube VAO for skybox
        self.cube_vao = self._create_cube_vao()
    
    def _create_gbuffer(self) -> Dict[str, Any]:
        """Create G-buffer for deferred rendering."""
        # Create FBO
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        
        # Create textures
        textures = {}
        
        # Position texture (RGBA16F)
        textures['gPosition'] = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textures['gPosition'])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, textures['gPosition'], 0)
        
        # Normal texture (RGB16F)
        textures['gNormal'] = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textures['gNormal'])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, textures['gNormal'], 0)
        
        # Albedo + Specular (RGBA8)
        textures['gAlbedoSpec'] = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textures['gAlbedoSpec'])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT2, GL_TEXTURE_2D, textures['gAlbedoSpec'], 0)
        
        # Tell OpenGL which color attachments we'll use for rendering
        attachments = [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2]
        glDrawBuffers(len(attachments), (GLenum * len(attachments))(*attachments))
        
        # Create and attach depth buffer
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
        
        # Check if framebuffer is complete
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("G-buffer framebuffer not complete!")
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        return {
            'fbo': fbo,
            'textures': textures,
            'rbo': rbo
        }
    
    def _create_hdr_framebuffer(self) -> Dict[str, Any]:
        """Create HDR framebuffer for lighting."""
        # Create FBO
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        
        # Create HDR color buffer
        color_buffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, color_buffer)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color_buffer, 0)
        
        # Create depth buffer
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
        
        # Check if framebuffer is complete
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("HDR framebuffer not complete!")
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        return {
            'fbo': fbo,
            'color_buffer': color_buffer,
            'rbo': rbo
        }
    
    def _render_geometry_pass(self, scene, camera):
        """Render the geometry pass for deferred rendering.
        
        This pass renders all scene geometry into the G-buffer, storing:
        - Position (RGB) + Depth (A)
        - Normal (RGB) + Specular (A)
        - Albedo (RGB) + Roughness (A)
        - Metallic (R) + AO (G) + Emissive (B) + Material ID (A)
        """
        # Bind G-buffer FBO and clear it
        glBindFramebuffer(GL_FRAMEBUFFER, self.g_buffer['fbo'])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Enable depth testing and face culling
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Get view and projection matrices
        view_matrix = camera.get_view_matrix()
        projection_matrix = camera.get_projection_matrix()
        
        # Use the geometry shader
        shader = self.shaders['geometry']
        shader.use()
        
        # Set view and projection matrices
        shader.set_mat4('view', view_matrix)
        shader.set_mat4('projection', projection_matrix)
        
        # Render all objects in the scene
        for obj in scene.get_objects():
            # Skip objects that don't have a mesh or are not visible
            if not hasattr(obj, 'mesh') or not obj.visible:
                continue
                
            # Get model matrix
            model_matrix = obj.get_transform_matrix()
            normal_matrix = glm.transpose(glm.inverse(glm.mat3(view_matrix * model_matrix)))
            
            # Set model and normal matrices
            shader.set_mat4('model', model_matrix)
            shader.set_mat3('normalMatrix', normal_matrix)
            
            # Set material properties
            material = obj.material if hasattr(obj, 'material') else self.default_material
            shader.set_vec3('material.albedo', material.albedo)
            shader.set_float('material.metallic', material.metallic)
            shader.set_float('material.roughness', material.roughness)
            shader.set_float('material.ao', material.ao)
            shader.set_vec3('material.emission', material.emission)
            shader.set_float('material.emission_strength', material.emission_strength)
            
            # Bind textures if they exist
            if material.albedo_map is not None:
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, material.albedo_map)
                shader.set_int('material.albedoMap', 0)
                shader.set_bool('material.hasAlbedoMap', True)
            else:
                shader.set_bool('material.hasAlbedoMap', False)
                
            if material.normal_map is not None:
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, material.normal_map)
                shader.set_int('material.normalMap', 1)
                shader.set_bool('material.hasNormalMap', True)
            else:
                shader.set_bool('material.hasNormalMap', False)
                
            if material.metallic_map is not None:
                glActiveTexture(GL_TEXTURE2)
                glBindTexture(GL_TEXTURE_2D, material.metallic_map)
                shader.set_int('material.metallicMap', 2)
                shader.set_bool('material.hasMetallicMap', True)
            else:
                shader.set_bool('material.hasMetallicMap', False)
                
            if material.roughness_map is not None:
                glActiveTexture(GL_TEXTURE3)
                glBindTexture(GL_TEXTURE_2D, material.roughness_map)
                shader.set_int('material.roughnessMap', 3)
                shader.set_bool('material.hasRoughnessMap', True)
            else:
                shader.set_bool('material.hasRoughnessMap', False)
                
            if material.ao_map is not None:
                glActiveTexture(GL_TEXTURE4)
                glBindTexture(GL_TEXTURE_2D, material.ao_map)
                shader.set_int('material.aoMap', 4)
                shader.set_bool('material.hasAOMap', True)
            else:
                shader.set_bool('material.hasAOMap', False)
            
            # Draw the mesh
            obj.mesh.draw()
            
            # Update statistics
            self.stats['draw_calls'] += 1
            self.stats['triangles'] += len(obj.mesh.indices) // 3
        
        # Unbind the G-buffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        # Restore OpenGL state
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
    
    def render_scene(self, scene, camera, shadow_maps=None):
        """Render the entire scene using the HDR pipeline.
        
        This is the main rendering function that coordinates all the render passes:
        1. Geometry pass: Render scene geometry into G-buffer
        2. Shadow pass: Generate shadow maps (if enabled)
        3. Lighting pass: Calculate direct and indirect lighting
        4. Post-processing: Apply bloom, tone mapping, and other effects
        
        Args:
            scene: The scene containing objects and lights to render
            camera: The camera to render from
            shadow_maps: Optional pre-computed shadow maps
        """
        # Start timing the frame
        frame_start_time = time.time()
        
        # Reset statistics
        self.stats['draw_calls'] = 0
        self.stats['triangles'] = 0
        self.stats['lights_processed'] = 0
        
        # Update camera matrices
        camera.update()
        
        # 1. Geometry pass: render scene into G-buffer
        self._render_geometry_pass(scene, camera)
        
        # 2. Shadow pass (if needed and not provided)
        if shadow_maps is None and hasattr(self, '_render_shadow_pass'):
            shadow_maps = self._render_shadow_pass(scene, camera)
        
        # 3. Lighting pass: calculate lighting using G-buffer
        self._render_lighting_pass(scene, camera, shadow_maps)
        
        # 4. Post-processing (bloom, tone mapping, etc.)
        if self.hdr_enabled:
            self._render_post_processing(scene, camera)
        
        # Update frame time
        self.stats['frame_time'] = (time.time() - frame_start_time) * 1000  # in ms
        
        # Print debug info (can be toggled)
        if hasattr(self, 'debug') and self.debug:
            self._print_debug_info()
    
    def _print_debug_info(self):
        """Print debug information about the current frame."""
        print(f"Frame time: {self.stats['frame_time']:.2f}ms | "
              f"Draw calls: {self.stats['draw_calls']} | "
              f"Triangles: {self.stats['triangles']} | "
              f"Lights: {self.stats['lights_processed']}", end='\r')
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        # Clean up shaders
        for shader in self.shaders.values():
            if hasattr(shader, 'delete'):
                shader.delete()
        
        # Clean up framebuffers
        if hasattr(self, 'g_buffer'):
            glDeleteFramebuffers(1, [self.g_buffer['fbo']])
            glDeleteTextures(list(self.g_buffer['textures'].values()))
            glDeleteRenderbuffers(1, [self.g_buffer['rbo']])
        
        if hasattr(self, 'hdr_fbo'):
            glDeleteFramebuffers(1, [self.hdr_fbo['fbo']])
            glDeleteTextures([self.hdr_fbo['color_buffer']])
            glDeleteRenderbuffers(1, [self.hdr_fbo['rbo']])
        
        if hasattr(self, 'bloom_fbo'):
            glDeleteFramebuffers(2, self.bloom_fbo['pingpong_fbos'])
            glDeleteTextures(self.bloom_fbo['pingpong_buffers'])
        
        # Clean up VAOs and VBOs
        if hasattr(self, 'quad_vao'):
            glDeleteVertexArrays(1, [self.quad_vao])
        
        # Clean up other OpenGL resources
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glUseProgram(0)
    
    def _render_lighting_pass(self, scene, camera, shadow_maps=None):
        """Render the lighting pass using the G-buffer.
        
        This pass calculates direct and indirect lighting using the G-buffer data
        and applies it to the scene.
        
        Args:
            scene: The scene containing lights and objects
            camera: The camera to render from
            shadow_maps: Optional dictionary of shadow maps from shadow pass
        """
        # Bind the HDR framebuffer and clear it
        glBindFramebuffer(GL_FRAMEBUFFER, self.hdr_fbo['fbo'])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Enable additive blending for multiple lights
        glEnable(GL_BLEND)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_ONE, GL_ONE)
        
        # Use the lighting shader
        shader = self.shaders['lighting']
        shader.use()
        
        # Set G-buffer textures
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.g_buffer['textures']['gPosition'])
        shader.set_int('gPosition', 0)
        
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.g_buffer['textures']['gNormal'])
        shader.set_int('gNormal', 1)
        
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.g_buffer['textures']['gAlbedoSpec'])
        shader.set_int('gAlbedoSpec', 2)
        
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self.g_buffer['textures']['gMetallicRoughnessAO'])
        shader.set_int('gMetallicRoughnessAO', 3)
        
        # Set camera position
        shader.set_vec3('viewPos', camera.position)
        
        # Set shadow map if available
        if shadow_maps and 'directional' in shadow_maps:
            glActiveTexture(GL_TEXTURE4)
            glBindTexture(GL_TEXTURE_2D, shadow_maps['directional'])
            shader.set_int('shadowMap', 4)
            shader.set_bool('useShadows', True)
            
            # Set shadow matrix if available
            if 'shadow_matrix' in shadow_maps:
                shader.set_mat4('lightSpaceMatrix', shadow_maps['shadow_matrix'])
        else:
            shader.set_bool('useShadows', False)
        
        # Set IBL maps if available
        if hasattr(self, 'irradiance_map') and hasattr(self, 'prefilter_map') and hasattr(self, 'brdf_lut'):
            glActiveTexture(GL_TEXTURE5)
            glBindTexture(GL_TEXTURE_CUBE_MAP, self.irradiance_map)
            shader.set_int('irradianceMap', 5)
            
            glActiveTexture(GL_TEXTURE6)
            glBindTexture(GL_TEXTURE_CUBE_MAP, self.prefilter_map)
            shader.set_int('prefilterMap', 6)
            
            glActiveTexture(GL_TEXTURE7)
            glBindTexture(GL_TEXTURE_2D, self.brdf_lut)
            shader.set_int('brdfLUT', 7)
            
            shader.set_bool('useIBL', True)
        else:
            shader.set_bool('useIBL', False)
        
        # Render lights
        for i, light in enumerate(scene.get_lights()):
            # Skip disabled lights
            if not light.enabled:
                continue
                
            # Set light properties based on type
            if light.type == LightType.DIRECTIONAL:
                shader.set_int('light.type', 0)
                shader.set_vec3('light.direction', light.direction)
            elif light.type == LightType.POINT:
                shader.set_int('light.type', 1)
                shader.set_vec3('light.position', light.position)
                shader.set_float('light.constant', light.constant)
                shader.set_float('light.linear', light.linear)
                shader.set_float('light.quadratic', light.quadratic)
            elif light.type == LightType.SPOT:
                shader.set_int('light.type', 2)
                shader.set_vec3('light.position', light.position)
                shader.set_vec3('light.direction', light.direction)
                shader.set_float('light.cutOff', light.cut_off)
                shader.set_float('light.outerCutOff', light.outer_cut_off)
                shader.set_float('light.constant', light.constant)
                shader.set_float('light.linear', light.linear)
                shader.set_float('light.quadratic', light.quadratic)
            
            # Set common light properties
            shader.set_vec3('light.color', light.color)
            shader.set_float('light.intensity', light.intensity)
            
            # For area lights
            if light.type == LightType.AREA:
                shader.set_vec3('light.position', light.position)
                shader.set_vec3('light.right', light.right)
                shader.set_vec3('light.up', light.up)
                shader.set_float('light.width', light.width)
                shader.set_float('light.height', light.height)
            
            # Render fullscreen quad for each light
            self._render_quad()
            
            # Update statistics
            self.stats['lights_processed'] += 1
        
        # Disable blending for next pass
        glDisable(GL_BLEND)
        
        # Unbind textures
        for i in range(8):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(GL_TEXTURE_2D, 0)
            glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
        
        # Unbind framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    def _render_quad(self):
        """Render a fullscreen quad for post-processing effects."""
        if not hasattr(self, 'quad_vao'):
            # Initialize quad VAO if it doesn't exist
            quad_vertices = np.array([
                # positions        # texture Coords
                -1.0,  1.0, 0.0,  0.0, 1.0,
                -1.0, -1.0, 0.0,  0.0, 0.0,
                 1.0,  1.0, 0.0,  1.0, 1.0,
                 1.0, -1.0, 0.0,  1.0, 0.0,
            ], dtype='f4')
            
            self.quad_vao = glGenVertexArrays(1)
            vbo = glGenBuffers(1)
            
            glBindVertexArray(self.quad_vao)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
            # Texture coord attribute
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))
            
            glBindVertexArray(0)
        
        # Render the quad
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        self._create_framebuffers()
        
        # Lighting and shadow setup
        self.lights: List[Light] = []
        self.ambient_light = (0.03, 0.03, 0.03)
        
        # Post-processing effects
        self.bloom_enabled = True
        self.bloom_threshold = 1.0
        self.bloom_strength = 1.5
        self.bloom_radius = 4.0
        
        # Atmospheric effects
        self.atmosphere_enabled = True
        self.fog_density = 0.01
        self.fog_color = (0.5, 0.6, 0.7)
        
        # Load shaders
        self._load_shaders()
    
    def _create_framebuffers(self):
        """Create framebuffers for HDR rendering and post-processing."""
        # Main HDR framebuffer
        self.hdr_color = self.ctx.texture((self.width, self.height), 4, dtype='f2')
        self.depth_buffer = self.ctx.depth_texture((self.width, self.height))
        self.hdr_fbo = self.ctx.framebuffer(
            color_attachments=[self.hdr_color],
            depth_attachment=self.depth_buffer
        )
        
        # Bloom effect buffers
        self.bloom_textures = []
        for i in range(2):
            tex = self.ctx.texture((self.width, self.height), 4, dtype='f2')
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.bloom_textures.append(tex)
        
        self.bloom_fbo = self.ctx.framebuffer(color_attachments=self.bloom_textures)
        
        # Ping-pong framebuffers for blur
        self.pingpong_fbos = []
        self.pingpong_textures = []
        for i in range(2):
            tex = self.ctx.texture((self.width, self.height), 4, dtype='f2')
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            fbo = self.ctx.framebuffer(color_attachments=[tex])
            self.pingpong_textures.append(tex)
            self.pingpong_fbos.append(fbo)
    
    def _load_shaders(self):
        """Load and compile shaders."""
        # Vertex shader for basic rendering
        self.shader_basic = self.ctx.program(
            vertex_shader="""
            #version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec3 aNormal;
            layout (location = 2) in vec2 aTexCoords;
            
            out vec3 FragPos;
            out vec3 Normal;
            out vec2 TexCoords;
            
            uniform mat4 model;
            uniform mat4 view;
            uniform mat4 projection;
            
            void main() {
                FragPos = vec3(model * vec4(aPos, 1.0));
                Normal = mat3(transpose(inverse(model))) * aNormal;
                TexCoords = aTexCoords;
                gl_Position = projection * view * vec4(FragPos, 1.0);
            }
            """,
            fragment_shader="""
            #version 330 core
            out vec4 FragColor;
            
            in vec3 FragPos;
            in vec3 Normal;
            in vec2 TexCoords;
            
            uniform vec3 viewPos;
            uniform vec3 albedo;
            uniform float metallic;
            uniform float roughness;
            uniform float ao;
            
            // IBL
            uniform samplerCube irradianceMap;
            uniform samplerCube prefilterMap;
            uniform sampler2D brdfLUT;
            
            // Lights
            #define MAX_LIGHTS 32
            uniform int numLights;
            uniform vec3 lightPositions[MAX_LIGHTS];
            uniform vec3 lightColors[MAX_LIGHTS];
            
            const float PI = 3.14159265359;
            
            // PBR functions here...
            
            void main() {
                // PBR shading calculations
                vec3 N = normalize(Normal);
                vec3 V = normalize(viewPos - FragPos);
                
                // Calculate reflectance at normal incidence
                vec3 F0 = vec3(0.04);
                F0 = mix(F0, albedo, metallic);
                
                // Reflectance equation
                vec3 Lo = vec3(0.0);
                
                // Calculate per-light radiance
                for(int i = 0; i < numLights; i++) {
                    // Calculate per-light radiance
                    // ...
                }
                
                // Add ambient IBL
                vec3 ambient = vec3(0.03) * albedo * ao;
                
                vec3 color = ambient + Lo;
                
                // HDR tone mapping
                color = color / (color + vec3(1.0));
                // Gamma correction
                color = pow(color, vec3(1.0/2.2));
                
                FragColor = vec4(color, 1.0);
            }
            """
        )
        
        # Post-processing shaders
        self.shader_bloom = self.ctx.program(
            vertex_shader="""
            #version 330 core
            layout (location = 0) in vec2 aPos;
            layout (location = 1) in vec2 aTexCoords;
            
            out vec2 TexCoords;
            
            void main() {
                gl_Position = vec4(aPos, 0.0, 1.0);
                TexCoords = aTexCoords;
            }
            """,
            fragment_shader="""
            #version 330 core
            out vec4 FragColor;
            
            in vec2 TexCoords;
            
            uniform sampler2D image;
            uniform bool horizontal;
            uniform float weight[5] = float[] (0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
            
            void main() {
                vec2 tex_offset = 1.0 / textureSize(image, 0);
                vec3 result = texture(image, TexCoords).rgb * weight[0];
                
                if(horizontal) {
                    for(int i = 1; i < 5; ++i) {
                        result += texture(image, TexCoords + vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
                        result += texture(image, TexCoords - vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
                    }
                } else {
                    for(int i = 1; i < 5; ++i) {
                        result += texture(image, TexCoords + vec2(0.0, tex_offset.y * i)).rgb * weight[i];
                        result += texture(image, TexCoords - vec2(0.0, tex_offset.y * i)).rgb * weight[i];
                    }
                }
                
                FragColor = vec4(result, 1.0);
            }
            """
        )
    
    def add_light(self, light: Light) -> None:
        """Add a light source to the scene."""
        self.lights.append(light)
    
    def set_environment_map(self, path: str) -> None:
        """Load an HDR environment map for image-based lighting."""
        # Implementation for loading and processing HDR environment maps
        pass
    
    def render_scene(self, scene, camera) -> None:
        """Render the entire scene with HDR and post-processing effects."""
        # Bind HDR framebuffer
        self.hdr_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        # Set up camera matrices
        view = camera.get_view_matrix()
        projection = camera.get_projection_matrix()
        
        # Render all objects in the scene
        for obj in scene.objects:
            self._render_object(obj, view, projection)
        
        # Apply post-processing effects
        self._apply_post_processing()
        
        # Blit to default framebuffer
        self.ctx.screen.use()
        self.ctx.copy_framebuffer(self.hdr_fbo, self.ctx.screen)
    
    def _render_object(self, obj, view, projection):
        """Render a single object with PBR materials."""
        # Set up shader uniforms
        self.shader_basic['model'].write(obj.transform.get_matrix().T.astype('f4').tobytes())
        self.shader_basic['view'].write(view.T.astype('f4').tobytes())
        self.shader_basic['projection'].write(projection.T.astype('f4').tobytes())
        
        # Set material properties
        material = obj.material
        self.shader_basic['albedo'].value = material.albedo
        self.shader_basic['metallic'].value = material.metallic
        self.shader_basic['roughness'].value = material.roughness
        self.shader_basic['ao'].value = material.ao
        
        # Render the object
        obj.mesh.render(self.shader_basic)
    
    def _apply_bloom(self):
        """Apply bloom effect to the rendered scene."""
        if not self.bloom_enabled:
            return
            
        # Extract bright areas
        self.bloom_fbo.use()
        # ... bloom extraction shader ...
        
        # Blur bright areas
        horizontal = True
        for i in range(10):  # Number of blur passes
            self.pingpong_fbos[horizontal].use()
            self.shader_bloom['horizontal'].value = horizontal
            # ... render quad with blur shader ...
            horizontal = not horizontal
        
        # Combine with original
        self.ctx.screen.use()
        # ... combine shader ...
    
    def _apply_post_processing(self):
        """Apply all post-processing effects."""
        self._apply_bloom()
        # ... other post-processing effects ...
    
    def cleanup(self):
        """Clean up resources."""
        self.hdr_fbo.release()
        self.bloom_fbo.release()
        for fbo in self.pingpong_fbos:
            fbo.release()
        self.ctx.release()

# Example usage:
if __name__ == "__main__":
    # Initialize pygame and create a window
    pygame.init()
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
    
    # Create HDR renderer
    renderer = HDRRenderer(width, height, hdr_enabled=True)
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update game logic here
        
        # Clear the screen
        renderer.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        # Render the scene
        # renderer.render_scene(scene, camera)
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    # Cleanup
    renderer.cleanup()
    pygame.quit()
