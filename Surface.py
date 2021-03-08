import bpy
from math import *

# Settings
width = 800
height = 800
z_height = 0.25 # Displace modifier strength
tex_res = 1     # Texture resolution (1:1)
mesh_res = 4    # Mesh resolution (8:1)

# Change to return data (should be between 0-1)
scale = 20
def get_data(x, y):
    x -= width/2
    y -= height/2
    
    x /= scale
    y /= scale
    
    r = sqrt(x**2+y**2)
    return (sin(r) + 1)/2

# Change to get color (you can use the ones defined below)
def get_color(x, y):
    a = get_data(x, y)
    return lerp(a, (1, 0, 0), (0, 0, 1))
    
    
# Color maps:

## One color map (from dark to light)
def one_color(a, c):
    return lerp_n(
        a, [(0, 0, 0), c, (1, 1, 1)]
    )
    
# Linear interpolation between two colors
def lerp(a, c1, c2):
    return (
        (1-a)*c1[0] + a*c2[0],
        (1-a)*c1[1] + a*c2[1],
        (1-a)*c1[2] + a*c2[2]
    )

# Linear interpolation between n_colors
def lerp_n(a, colors):
    if a == 1: return colors[-1]
    n = len(colors) - 1
    s = floor(a*n)
    b = a*n - s
    return lerp(b, colors[s], colors[s+1])
    
# Rainbow colors
def rainbow(a):
    return lerp_n(
            a,
            [
                (1, 0, 0), # red
                (1, 1, 0), # yellow
                (0, 1, 0), # green
                (0, 1, 1), # cyan
                (0, 0, 1), # blue
                (1, 0, 1)  # magenta
            ]
        )


# Variables
mesh_width = int(width/mesh_res)
mesh_height = int(height/mesh_res)
tex_width = int(width/tex_res)
tex_height = int(height/tex_res)
size = 2
aspect_ratio = width/height



# Create and name a grid
bpy.ops.mesh.primitive_grid_add(x_subdivisions=mesh_width, y_subdivisions=mesh_height ,size=size, location=(0, 0, 0))
plotObject = bpy.context.active_object
plotObject.name = 'Surface Plot'

# Size grid  properly
plotObject.scale[0] = aspect_ratio
plotObject.scale[1] = 1



# Generate a displace and diffuse map
displace_image = bpy.data.images.new("Displace Map", width=tex_width, height=tex_height)
diffuse_image = bpy.data.images.new("Diffuse Map", width=tex_width, height=tex_height)

displace_pixels = [None] * tex_width * tex_height
diffuse_pixels = [None] * tex_width * tex_height

for x in range(tex_width):
    for y in range(tex_height):
        a = get_data(x, y)
        displace_pixels[(y * tex_width) + x] = [a, a, a, 1.0]
        
        r, g, b = get_color(x, y)
        diffuse_pixels[(y * tex_width) + x] = [r, g, b, 1.0]

displace_pixels = [chan for px in displace_pixels for chan in px]
diffuse_pixels = [chan for px in diffuse_pixels for chan in px]

displace_image.pixels = displace_pixels
diffuse_image.pixels = diffuse_pixels

# Create a displace texture
displace_map = bpy.data.textures.new('Displace Texture', type='IMAGE')
displace_map.image = displace_image

# Create a displace modifier
displace_mode = plotObject.modifiers.new("Displace", type='DISPLACE')
displace_mode.texture = displace_map
displace_mode.strength = z_height



# Create a material
material = bpy.data.materials.new(name="Plot Material")
# Use nodes
material.use_nodes = True
# Add Principled BSDF
bsdf = material.node_tree.nodes["Principled BSDF"]
# Add an ImageTexture
diffuse_map = material.node_tree.nodes.new('ShaderNodeTexImage')
# Set diffuse image
diffuse_map.image = diffuse_image
# Link ImageTexture to Principled BSDF
material.node_tree.links.new(bsdf.inputs['Base Color'], diffuse_map.outputs['Color'])



# Assign it to object
if plotObject.data.materials:
    plotObject.data.materials[0] = material
else:
    plotObject.data.materials.append(material)



# Shade smooth
mesh = bpy.context.active_object.data
for f in mesh.polygons:
    f.use_smooth = True