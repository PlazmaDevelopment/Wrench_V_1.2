"""
Shader definitions for the Wrench HDR renderer.

This module contains all shader code used by the HDR renderer,
including PBR materials, lighting, post-processing, and effects.
"""

# =============================================================================
# PBR Shaders
# =============================================================================

PBR_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec3 a_Position;
layout (location = 1) in vec3 a_Normal;
layout (location = 2) in vec2 a_TexCoords;
layout (location = 3) in vec3 a_Tangent;
layout (location = 4) in vec3 a_Bitangent;

// Outputs to fragment shader
out vec3 v_FragPos;
out vec2 v_TexCoords;
out vec3 v_Normal;
out mat3 v_TBN;

// Uniforms
uniform mat4 u_Model;
uniform mat4 u_View;
uniform mat4 u_Projection;
uniform mat3 u_NormalMatrix;

void main() {
    // Calculate vertex position in world space
    vec4 worldPos = u_Model * vec4(a_Position, 1.0);
    v_FragPos = worldPos.xyz;
    
    // Pass texture coordinates
    v_TexCoords = a_TexCoords;
    
    // Transform normal to world space
    v_Normal = normalize(u_NormalMatrix * a_Normal);
    
    // Calculate TBN matrix for normal mapping
    vec3 T = normalize(u_NormalMatrix * a_Tangent);
    vec3 B = normalize(u_NormalMatrix * a_Bitangent);
    vec3 N = v_Normal;
    v_TBN = mat3(T, B, N);
    
    // Final vertex position
    gl_Position = u_Projection * u_View * worldPos;
}
"""

PBR_FRAGMENT_SHADER = """#version 460 core
// Inputs from vertex shader
in vec3 v_FragPos;
in vec2 v_TexCoords;
in vec3 v_Normal;
in mat3 v_TBN;

// Outputs
layout (location = 0) out vec4 gPosition;
layout (location = 1) out vec4 gNormal;
layout (location = 2) out vec4 gAlbedoSpec;

// Material properties
struct Material {
    // Base color
    sampler2D albedoMap;
    vec4 albedoColor;
    
    // Normal map
    sampler2D normalMap;
    float normalStrength;
    
    // PBR maps
    sampler2D metallicMap;
    sampler2D roughnessMap;
    sampler2D aoMap;
    
    // Material properties
    float metallic;
    float roughness;
    float ao;
    
    // Emissive
    sampler2D emissiveMap;
    vec3 emissiveColor;
    float emissiveIntensity;
    
    // Clearcoat
    float clearcoat;
    float clearcoatRoughness;
    
    // Subsurface scattering
    float subsurface;
    vec3 subsurfaceColor;
    
    // Sheen
    float sheen;
    vec3 sheenTint;
    
    // Anisotropy
    float anisotropy;
    float anisotropyRotation;
    
    // IOR
    float ior;
    
    // Transmission
    float transmission;
    
    // Alpha
    float alpha;
    float alphaCutoff;
    
    // UV tiling and offset
    vec2 uvScale;
    vec2 uvOffset;
};

// Uniforms
uniform Material u_Material;
uniform vec3 u_ViewPos;

void main() {
    // Apply UV scaling and offset
    vec2 texCoords = v_TexCoords * u_Material.uvScale + u_Material.uvOffset;
    
    // Sample textures
    vec4 albedo = texture(u_Material.albedoMap, texCoords) * u_Material.albedoColor;
    
    // Alpha testing
    if (albedo.a < u_Material.alphaCutoff) {
        discard;
    }
    
    // Sample and decode normal from normal map
    vec3 normal = v_Normal;
    if (u_Material.normalStrength > 0.0) {
        normal = texture(u_Material.normalMap, texCoords).rgb;
        normal = normalize(normal * 2.0 - 1.0);
        normal = normalize(v_TBN * normal);
        normal = mix(v_Normal, normal, u_Material.normalStrength);
    }
    
    // Sample PBR maps
    float metallic = texture(u_Material.metallicMap, texCoords).r * u_Material.metallic;
    float roughness = texture(u_Material.roughnessMap, texCoords).r * u_Material.roughness;
    float ao = texture(u_Material.aoMap, texCoords).r * u_Material.ao;
    
    // Store G-buffer
    gPosition = vec4(v_FragPos, 1.0);
    gNormal = vec4(normalize(normal) * 0.5 + 0.5, 1.0);
    gAlbedoSpec = vec4(albedo.rgb, metallic);
    
    // Optional: Store roughness and AO in alpha channels
    // gNormal.a = roughness;
    // gAlbedoSpec.a = ao;
}
"""

# =============================================================================
# Lighting Shaders
# =============================================================================

LIGHTING_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec3 a_Position;

uniform mat4 u_Model;
uniform mat4 u_View;
uniform mat4 u_Projection;

void main() {
    gl_Position = u_Projection * u_View * u_Model * vec4(a_Position, 1.0);
}
"""

LIGHTING_FRAGMENT_SHADER = """#version 460 core
out vec4 FragColor;

// G-buffer inputs
uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D gAlbedoSpec;

// Shadow maps
uniform sampler2D u_ShadowMaps[4];
uniform int u_NumShadowMaps;

// Light structure
struct Light {
    vec3 position;
    vec3 color;
    float intensity;
    float radius;
    int type;  // 0 = directional, 1 = point, 2 = spot
    vec3 direction;
    float innerCutoff;
    float outerCutoff;
    bool castShadows;
    int shadowMapIndex;
};

// Uniforms
uniform Light u_Lights[32];
uniform int u_NumLights;
uniform vec3 u_ViewPos;
uniform mat4 u_LightSpaceMatrices[4];

// PBR functions
const float PI = 3.14159265359;

// Normal Distribution Function (GGX/Trowbridge-Reitz)
float DistributionGGX(vec3 N, vec3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    
    float nom = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;
    
    return nom / max(denom, 0.001);
}

// Geometry Function (Schlick-GGX)
float GeometrySchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    
    float nom = NdotV;
    float denom = NdotV * (1.0 - k) + k;
    
    return nom / denom;
}

// Geometry Smith
float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx1 = GeometrySchlickGGX(NdotV, roughness);
    float ggx2 = GeometrySchlickGGX(NdotL, roughness);
    
    return ggx1 * ggx2;
}

// Fresnel Schlick approximation
vec3 FresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// Shadow calculation
float CalculateShadow(vec4 fragPosLightSpace, sampler2D shadowMap, vec3 normal, vec3 lightDir) {
    // Perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    
    // Transform to [0,1] range
    projCoords = projCoords * 0.5 + 0.5;
    
    // Get closest depth value from light's perspective
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    
    // Get depth of current fragment from light's perspective
    float currentDepth = projCoords.z;
    
    // Check if current fragment is in shadow
    float bias = max(0.05 * (1.0 - dot(normal, lightDir)), 0.005);
    
    // PCF for softer shadows
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    for(int x = -1; x <= 1; ++x) {
        for(int y = -1; y <= 1; ++y) {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;
        }
    }
    shadow /= 9.0;
    
    // Keep shadow at 0.0 when outside the far plane region of the light's frustum
    if(projCoords.z > 1.0) {
        shadow = 0.0;
    }
    
    return shadow;
}

void main() {
    // Retrieve data from G-buffer
    vec3 FragPos = texture(gPosition, gl_FragCoord.xy / textureSize(gPosition, 0)).rgb;
    vec3 Normal = texture(gNormal, gl_FragCoord.xy / textureSize(gNormal, 0)).rgb * 2.0 - 1.0;
    vec4 albedoSpec = texture(gAlbedoSpec, gl_FragCoord.xy / textureSize(gAlbedoSpec, 0));
    
    vec3 albedo = albedoSpec.rgb;
    float metallic = albedoSpec.a;
    
    // Hardcoded values for now
    float roughness = 0.5;
    float ao = 1.0;
    
    // Calculate view direction
    vec3 viewDir = normalize(u_ViewPos - FragPos);
    
    // Calculate reflectance at normal incidence
    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, metallic);
    
    // Reflectance equation
    vec3 Lo = vec3(0.0);
    
    // Calculate per-light radiance
    for(int i = 0; i < u_NumLights; i++) {
        Light light = u_Lights[i];
        
        // Calculate radiance
        vec3 lightDir;
        vec3 radiance;
        
        if(light.type == 0) { // Directional light
            lightDir = normalize(-light.direction);
            radiance = light.color * light.intensity;
        } else if(light.type == 1) { // Point light
            vec3 lightVector = light.position - FragPos;
            float distance = length(lightVector);
            lightDir = normalize(lightVector);
            
            // Attenuation
            float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * (distance * distance));
            radiance = light.color * light.intensity * attenuation;
        } else { // Spot light
            vec3 lightVector = light.position - FragPos;
            float distance = length(lightVector);
            lightDir = normalize(lightVector);
            
            // Attenuation
            float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * (distance * distance));
            
            // Spotlight intensity
            float theta = dot(lightDir, normalize(-light.direction));
            float epsilon = light.innerCutoff - light.outerCutoff;
            float intensity = clamp((theta - light.outerCutoff) / epsilon, 0.0, 1.0);
            
            radiance = light.color * light.intensity * attenuation * intensity;
        }
        
        // Calculate shadow
        float shadow = 0.0;
        if(light.castShadows && light.shadowMapIndex >= 0 && light.shadowMapIndex < u_NumShadowMaps) {
            vec4 fragPosLightSpace = u_LightSpaceMatrices[light.shadowMapIndex] * vec4(FragPos, 1.0);
            shadow = CalculateShadow(fragPosLightSpace, u_ShadowMaps[light.shadowMapIndex], Normal, lightDir);
        }
        
        // Calculate per-light radiance
        vec3 H = normalize(viewDir + lightDir);
        
        // Cook-Torrance BRDF
        float NDF = DistributionGGX(Normal, H, roughness);
        float G = GeometrySmith(Normal, viewDir, lightDir, roughness);
        vec3 F = FresnelSchlick(max(dot(H, viewDir), 0.0), F0);
        
        vec3 kS = F;
        vec3 kD = vec3(1.0) - kS;
        kD *= 1.0 - metallic;
        
        vec3 numerator = NDF * G * F;
        float denominator = 4.0 * max(dot(Normal, viewDir), 0.0) * max(dot(Normal, lightDir), 0.0) + 0.001;
        vec3 specular = numerator / denominator;
        
        // Add to outgoing radiance Lo
        float NdotL = max(dot(Normal, lightDir), 0.0);
        Lo += (kD * albedo / PI + specular) * radiance * NdotL * (1.0 - shadow);
    }
    
    // Ambient lighting (IBL would go here)
    vec3 ambient = vec3(0.03) * albedo * ao;
    
    // Final color
    vec3 color = ambient + Lo;
    
    // HDR tonemapping
    color = color / (color + vec3(1.0));
    
    // Gamma correction
    color = pow(color, vec3(1.0/2.2));
    
    FragColor = vec4(color, 1.0);
}
"""

# =============================================================================
# Post-Processing Shaders
# =============================================================================

POST_PROCESSING_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec2 a_Position;
layout (location = 1) in vec2 a_TexCoords;

out vec2 v_TexCoords;

void main() {
    v_TexCoords = a_TexCoords;
    gl_Position = vec4(a_Position, 0.0, 1.0);
}
"""

BLOOM_FRAGMENT_SHADER = """#version 460 core
out vec4 FragColor;

in vec2 v_TexCoords;

uniform sampler2D u_Scene;
uniform sampler2D u_BloomBlur;
uniform float u_Exposure;
uniform float u_BloomStrength;

void main() {
    const float gamma = 2.2;
    
    // Sample the HDR color buffer and bloom blur texture
    vec3 hdrColor = texture(u_Scene, v_TexCoords).rgb;      
    vec3 bloomColor = texture(u_BloomBlur, v_TexCoords).rgb;
    
    // Additive blending for bloom
    hdrColor += bloomColor * u_BloomStrength; // Add bloom effect
    
    // Tone mapping
    vec3 result = vec3(1.0) - exp(-hdrColor * u_Exposure);
    
    // Gamma correction
    result = pow(result, vec3(1.0 / gamma));
    
    FragColor = vec4(result, 1.0);
}
"""

SSAO_FRAGMENT_SHADER = """#version 460 core
out float FragColor;

in vec2 v_TexCoords;

uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D u_NoiseTexture;

// Parameters
uniform vec2 u_NoiseScale;
uniform int u_KernelSize;
uniform float u_Radius;
uniform float u_Bias;
uniform float u_Power;

// Array of kernel samples
uniform vec3 u_Samples[64];

// Tile noise texture over screen
vec2 noiseScale = vec2(1920.0/4.0, 1080.0/4.0);

void main() {
    // Get input for SSAO algorithm
    vec3 fragPos = texture(gPosition, v_TexCoords).xyz;
    vec3 normal = normalize(texture(gNormal, v_TexCoords).rgb * 2.0 - 1.0);
    vec3 randomVec = normalize(texture(u_NoiseTexture, v_TexCoords * u_NoiseScale).xyz);
    
    // Create TBN matrix
    vec3 tangent = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 TBN = mat3(tangent, bitangent, normal);
    
    // Calculate occlusion
    float occlusion = 0.0;
    for(int i = 0; i < u_KernelSize; ++i) {
        // Get sample position
        vec3 samplePos = TBN * u_Samples[i]; // From tangent to view-space
        samplePos = fragPos + samplePos * u_Radius;
        
        // Project sample position to sample texture
        vec4 offset = vec4(samplePos, 1.0);
        offset = u_Projection * offset; // From view to clip-space
        offset.xyz /= offset.w; // Perspective divide
        offset.xyz = offset.xyz * 0.5 + 0.5; // Transform to range 0.0 - 1.0
        
        // Get sample depth
        float sampleDepth = texture(gPosition, offset.xy).z;
        
        // Range check & accumulate
        float rangeCheck = smoothstep(0.0, 1.0, u_Radius / abs(fragPos.z - sampleDepth));
        occlusion += (sampleDepth >= samplePos.z + u_Bias ? 1.0 : 0.0) * rangeCheck;           
    }
    
    occlusion = 1.0 - (occlusion / u_KernelSize);
    FragColor = pow(occlusion, u_Power);
}
"""

TONE_MAPPING_FRAGMENT_SHADER = """#version 460 core
out vec4 FragColor;

in vec2 v_TexCoords;

uniform sampler2D u_HDRBuffer;
uniform float u_Exposure;
uniform bool u_UseACES;

// ACES tone mapping curve fit to go from HDR to LDR
// sRGB => XYZ => D65_2_AP1 => RRT_SAT
const mat3 ACESInputMat = mat3(
    0.59719, 0.35458, 0.04823,
    0.07600, 0.90834, 0.01566,
    0.02840, 0.13383, 0.83777
);

// ODT_SAT => XYZ => sRGB
const mat3 ACESOutputMat = mat3(
     1.60475, -0.53108, -0.07367,
    -0.10208,  1.10813, -0.00605,
    -0.00327, -0.07276,  1.07602
);

vec3 RRTAndODTFit(vec3 v) {
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return a / b;
}

vec3 ACESFitted(vec3 color) {
    color = color * ACESInputMat;
    color = RRTAndODTFit(color);
    color = ACESOutputMat * color;
    return clamp(color, 0.0, 1.0);
}

void main() {
    // Sample HDR color
    vec3 hdrColor = texture(u_HDRBuffer, v_TexCoords).rgb;
    
    // Exposure tone mapping
    vec3 mapped;
    if (u_UseACES) {
        // ACES filmic tone mapping
        mapped = ACESFitted(hdrColor * u_Exposure);
    } else {
        // Reinhard tone mapping
        mapped = vec3(1.0) - exp(-hdrColor * u_Exposure);
    }
    
    // Gamma correction
    mapped = pow(mapped, vec3(1.0 / 2.2));
    
    FragColor = vec4(mapped, 1.0);
}
"""

# =============================================================================
# Skybox Shader
# =============================================================================

SKYBOX_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec3 a_Position;

out vec3 v_TexCoords;

uniform mat4 u_Projection;
uniform mat4 u_View;

void main() {
    v_TexCoords = a_Position;
    vec4 pos = u_Projection * u_View * vec4(a_Position, 1.0);
    gl_Position = pos.xyww; // Force z to be 1.0 (furthest)
}
"""

SKYBOX_FRAGMENT_SHADER = """#version 460 core
out vec4 FragColor;

in vec3 v_TexCoords;

uniform samplerCube u_Skybox;
uniform vec3 u_SunDirection;
uniform vec3 u_SunColor;
uniform float u_Time;

// Constants
const float sunAngularRadius = 0.00465; // ~0.5 degrees in radians

// Simple atmospheric scattering approximation
vec3 atmosphere(vec3 rd, vec3 sunDir) {
    // Simple Rayleigh-like scattering
    float sunDot = max(dot(rd, sunDir), 0.0);
    float rayleigh = 3.0 / (8.0 * 3.14159265) * (1.0 + sunDot * sunDot);
    
    // Mie scattering (aerosols)
    float g = 0.8; // Scattering directionality
    float mie = (1.0 - g * g) / (4.0 * 3.14159265 * pow(1.0 + g * g - 2.0 * g * sunDot, 1.5));
    
    // Combine with colors
    vec3 skyColor = mix(
        vec3(0.3, 0.6, 1.0),  // Blue sky
        vec3(1.0, 0.7, 0.4),  // Sunset
        smoothstep(0.0, 1.0, -sunDir.y * 0.5 + 0.5)
    );
    
    // Add sun
    float sun = smoothstep(sunAngularRadius, 0.0, acos(sunDot));
    
    return skyColor * rayleigh + u_SunColor * mie + u_SunColor * sun * 10.0;
}

void main() {
    // Sample cubemap
    vec3 texColor = texture(u_Skybox, v_TexCoords).rgb;
    
    // Add atmospheric scattering
    vec3 dir = normalize(v_TexCoords);
    vec3 sunDir = normalize(u_SunDirection);
    vec3 atmosphereColor = atmosphere(dir, sunDir);
    
    // Blend between cubemap and atmosphere based on view direction
    float blend = smoothstep(0.0, 0.3, dir.y);
    vec3 color = mix(atmosphereColor, texColor, blend);
    
    // Apply exposure and gamma correction
    color = pow(color, vec3(1.0/2.2));
    
    FragColor = vec4(color, 1.0);
}
"""

# =============================================================================
# Shadow Mapping Shaders
# =============================================================================

SHADOW_MAP_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec3 a_Position;

uniform mat4 u_LightSpaceMatrix;
uniform mat4 u_Model;

void main() {
    gl_Position = u_LightSpaceMatrix * u_Model * vec4(a_Position, 1.0);
}
"""

SHADOW_MAP_FRAGMENT_SHADER = """#version 460 core
void main() {
    // Nothing to do here, we only need the depth values
}
"""

# =============================================================================
# Debug Shaders
# =============================================================================

DEBUG_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec3 a_Position;
layout (location = 1) in vec3 a_Color;

out vec3 v_Color;

uniform mat4 u_Model;
uniform mat4 u_View;
uniform mat4 u_Projection;

void main() {
    v_Color = a_Color;
    gl_Position = u_Projection * u_View * u_Model * vec4(a_Position, 1.0);
}
"""

DEBUG_FRAGMENT_SHADER = """#version 460 core
in vec3 v_Color;
out vec4 FragColor;

void main() {
    FragColor = vec4(v_Color, 1.0);
}
"""

# =============================================================================
# Fullscreen Quad Shader
# =============================================================================

FULLSCREEN_QUAD_VERTEX_SHADER = """#version 460 core
layout (location = 0) in vec2 a_Position;
layout (location = 1) in vec2 a_TexCoords;

out vec2 v_TexCoords;

void main() {
    v_TexCoords = a_TexCoords;
    gl_Position = vec4(a_Position, 0.0, 1.0);
}
"""

# =============================================================================
# Shader Dictionary
# =============================================================================

SHADERS = {
    # PBR shaders
    'pbr': {
        'vertex': PBR_VERTEX_SHADER,
        'fragment': PBR_FRAGMENT_SHADER
    },
    
    # Lighting shaders
    'lighting': {
        'vertex': LIGHTING_VERTEX_SHADER,
        'fragment': LIGHTING_FRAGMENT_SHADER
    },
    
    # Post-processing shaders
    'post': {
        'vertex': POST_PROCESSING_VERTEX_SHADER,
    },
    
    'bloom': {
        'fragment': BLOOM_FRAGMENT_SHADER
    },
    
    'ssao': {
        'fragment': SSAO_FRAGMENT_SHADER
    },
    
    'tone_mapping': {
        'fragment': TONE_MAPPING_FRAGMENT_SHADER
    },
    
    # Skybox shaders
    'skybox': {
        'vertex': SKYBOX_VERTEX_SHADER,
        'fragment': SKYBOX_FRAGMENT_SHADER
    },
    
    # Shadow mapping shaders
    'shadow_map': {
        'vertex': SHADOW_MAP_VERTEX_SHADER,
        'fragment': SHADOW_MAP_FRAGMENT_SHADER
    },
    
    # Debug shaders
    'debug': {
        'vertex': DEBUG_VERTEX_SHADER,
        'fragment': DEBUG_FRAGMENT_SHADER
    },
    
    # Fullscreen quad shader
    'fullscreen_quad': {
        'vertex': FULLSCREEN_QUAD_VERTEX_SHADER
    }
}
