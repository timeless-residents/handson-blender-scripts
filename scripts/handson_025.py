#!/usr/bin/env python3
"""
Blender Python script to create a night cityscape with emissive vertex colors.
This script renders a scene with buildings that have random emissive windows.
"""

import os
import random
import shutil
import time
from datetime import datetime
import bpy
from mathutils import Vector


def setup_environment():
    """Set up the Blender environment and clean the scene."""
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create world with dark sky
    world = bpy.data.worlds.new("NightWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs["Color"].default_value = (0.01, 0.01, 0.02, 1.0)
    bg_node.inputs["Strength"].default_value = 0.1

    # Create a new collection for our scene
    if "NightCity" not in bpy.data.collections:
        night_city = bpy.data.collections.new("NightCity")
        bpy.context.scene.collection.children.link(night_city)
    else:
        night_city = bpy.data.collections["NightCity"]
        
    return night_city


def create_building(collection, location, scale):
    """Create a building with random emissive windows."""
    # Create building mesh
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    building = bpy.context.active_object
    building.name = f"Building_{location[0]}_{location[1]}"
    building.scale = scale

    # Move to our collection
    old_collection = building.users_collection[0]
    old_collection.objects.unlink(building)
    collection.objects.link(building)

    # Subdivide for windows
    bpy.ops.object.select_all(action='DESELECT')
    building.select_set(True)
    bpy.context.view_layer.objects.active = building
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=6)  # Increased subdivisions for more windows
    bpy.ops.object.mode_set(mode='OBJECT')

    # Enable vertex colors
    if not building.data.vertex_colors:
        building.data.vertex_colors.new()
    color_layer = building.data.vertex_colors.active

    # Assign random emissive colors to vertices (windows)
    mesh = building.data
    for poly in mesh.polygons:
        # Only make front/side-facing polygons emissive (windows)
        # This makes windows appear on vertical faces
        if abs(poly.normal.z) < 0.5:  # Not top or bottom face
            window_probability = random.random()
            if window_probability > 0.6:  # 40% chance of a lit window
                # Warm light colors for lit windows
                r = random.uniform(0.9, 1.0)
                g = random.uniform(0.7, 0.9)
                b = random.uniform(0.2, 0.5)
                intensity = 1.0
            elif window_probability > 0.3:  # 30% chance of a dimly lit window
                # Dimmer, cooler light for some variation
                r = random.uniform(0.5, 0.8)
                g = random.uniform(0.5, 0.8)
                b = random.uniform(0.7, 0.9)
                intensity = 0.7
            else:  # 30% chance of a dark window
                # Very dark color for unlit windows
                r, g, b = 0.02, 0.02, 0.03
                intensity = 0.0
                
            # Apply the color to all vertices of this face
            for idx in poly.loop_indices:
                loop = mesh.loops[idx]
                color_layer.data[idx].color = (r, g, b, 1.0)
        else:
            # Building structure (non-window parts)
            for idx in poly.loop_indices:
                color_layer.data[idx].color = (0.05, 0.05, 0.07, 1.0)

    # Create material with vertex color as emission
    mat = bpy.data.materials.new(name=f"Building_Mat_{location[0]}_{location[1]}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create nodes
    output = nodes.new(type='ShaderNodeOutputMaterial')
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    vertex_color = nodes.new(type='ShaderNodeVertexColor')
    emission = nodes.new(type='ShaderNodeEmission')
    mix_shader = nodes.new(type='ShaderNodeMixShader')
    
    # Position nodes for better organization
    output.location = Vector((300, 0))
    mix_shader.location = Vector((100, 0))
    principled.location = Vector((-100, 100))
    emission.location = Vector((-100, -100))
    vertex_color.location = Vector((-300, -100))

    # Set up node properties
    vertex_color.layer_name = color_layer.name
    principled.inputs['Base Color'].default_value = (0.05, 0.05, 0.07, 1.0)  # Dark building color
    
    # Set Metallic and Roughness
    if 'Metallic' in principled.inputs:
        principled.inputs['Metallic'].default_value = 0.2
    if 'Roughness' in principled.inputs:
        principled.inputs['Roughness'].default_value = 0.8
    
    # Set up emission strength
    emission.inputs['Strength'].default_value = 5.0  # Increased emission strength
    
    # Connect nodes
    links.new(vertex_color.outputs['Color'], emission.inputs['Color'])
    links.new(principled.outputs['BSDF'], mix_shader.inputs[1])
    links.new(emission.outputs['Emission'], mix_shader.inputs[2])
    
    # Create a simpler method to use vertex color brightness as mix factor
    # Instead of RGB2BW node, we'll use a Math node
    math_node = nodes.new(type='ShaderNodeMath')
    math_node.location = Vector((-100, 0))
    math_node.operation = 'ADD'
    
    # Create RGB Separate node to get individual RGB components
    separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
    separate_rgb.location = Vector((-300, 0))
    
    # Connect vertex color to separate RGB
    links.new(vertex_color.outputs['Color'], separate_rgb.inputs['Image'])
    
    # Add R+G+B and divide by 3 to get approximate brightness
    links.new(separate_rgb.outputs['R'], math_node.inputs[0])
    links.new(separate_rgb.outputs['G'], math_node.inputs[1])
    
    # Add another Math node for the blue component
    math_node2 = nodes.new(type='ShaderNodeMath')
    math_node2.location = Vector((-100, 50))
    math_node2.operation = 'ADD'
    
    links.new(math_node.outputs['Value'], math_node2.inputs[0])
    links.new(separate_rgb.outputs['B'], math_node2.inputs[1])
    
    # Divide by 3 to get average
    math_node3 = nodes.new(type='ShaderNodeMath')
    math_node3.location = Vector((0, 50))
    math_node3.operation = 'DIVIDE'
    math_node3.inputs[1].default_value = 3.0  # Divide by 3
    
    links.new(math_node2.outputs['Value'], math_node3.inputs[0])
    
    # Use this brightness value for mix factor
    links.new(math_node3.outputs['Value'], mix_shader.inputs['Fac'])
    
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    # Assign material to building
    if building.data.materials:
        building.data.materials[0] = mat
    else:
        building.data.materials.append(mat)

    return building


def create_city_scene(collection):
    """Create a city scene with multiple buildings."""
    buildings = []

    # Create ground plane
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -0.1))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    # Move to our collection
    old_collection = ground.users_collection[0]
    old_collection.objects.unlink(ground)
    collection.objects.link(ground)
    
    # Add material to ground
    mat = bpy.data.materials.new(name="Ground_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes["Principled BSDF"]
    principled.inputs['Base Color'].default_value = (0.01, 0.01, 0.015, 1.0)  # Darker ground
    
    # Check if 'Roughness' exists before setting
    if 'Roughness' in principled.inputs:
        principled.inputs['Roughness'].default_value = 0.95
    
    if ground.data.materials:
        ground.data.materials[0] = mat
    else:
        ground.data.materials.append(mat)

    # Create multiple buildings with random positions and scales
    for i in range(-5, 6, 2):
        for j in range(-5, 6, 2):
            # Skip some positions for variation
            if random.random() < 0.2:  # 20% chance to skip
                continue
                
            location = (i + random.uniform(-0.8, 0.8), 
                       j + random.uniform(-0.8, 0.8), 
                       random.uniform(0.5, 3.0))
            
            # More varied building sizes
            height = random.uniform(2.0, 6.0)
            width = random.uniform(0.6, 1.5)
            depth = random.uniform(0.6, 1.5)
            scale = (width, depth, height)
            
            building = create_building(collection, location, scale)
            buildings.append(building)

    return buildings


def setup_camera_and_lighting():
    """Set up camera and lighting for the scene."""
    # Create an empty as target
    empty = bpy.data.objects.new("CameraTarget", None)
    empty.location = (0, 0, 3)
    bpy.context.scene.collection.objects.link(empty)
    
    # Create camera
    bpy.ops.object.camera_add(location=(15, -15, 10), rotation=(1.0, 0.0, 0.8))
    camera = bpy.context.active_object
    camera.name = "NightCamera"
    
    # Make this the active camera
    bpy.context.scene.camera = camera
    
    # Add camera constraint to look at scene center
    track_to = camera.constraints.new(type='TRACK_TO')
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'
    track_to.target = empty
    
    # Add a slight ambient light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.name = "NightSun"
    sun.data.energy = 0.05  # Reduced energy for darker scene
    sun.data.color = (0.1, 0.1, 0.2)
    
    # Add a moon light
    bpy.ops.object.light_add(type='AREA', location=(8, -8, 15))
    moon = bpy.context.active_object
    moon.name = "Moon"
    moon.data.energy = 10.0  # Increased for more dramatic lighting
    moon.data.color = (0.8, 0.9, 1.0)
    moon.rotation_euler = (0.5, 0.2, 0.8)
    moon.data.size = 5.0


def setup_render_settings():
    """Configure render settings for faster rendering."""
    render = bpy.context.scene.render
    
    # Set output resolution
    render.resolution_x = 1280
    render.resolution_y = 720
    
    # Check if film_transparent exists before setting
    if hasattr(render, 'film_transparent'):
        render.film_transparent = False  # Ensure background is visible
    
    # Use Eevee Next for faster rendering
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    
    # Configure Eevee Next settings for better quality
    eevee_next = bpy.context.scene.eevee
    
    # Try to enable specific Eevee Next features if available
    if hasattr(eevee_next, 'bloom_intensity'):
        eevee_next.bloom_intensity = 0.2  # Increased bloom
        
    # Try to set view transform if available
    try:
        bpy.context.scene.view_settings.view_transform = 'Filmic'
    except:
        print("Could not set view transform to Filmic")

    # Try to set look if available
    try:
        bpy.context.scene.view_settings.look = 'Medium Contrast'
    except:
        print("Could not set look to Medium Contrast")
    
    # Set exposure and gamma (should be available in all versions)
    bpy.context.scene.view_settings.exposure = 0.0
    bpy.context.scene.view_settings.gamma = 1.0


def ensure_output_directory():
    """Create output directory if it doesn't exist and handle existing files."""
    # Get the directory of the current blend file
    blend_dir = os.path.dirname(bpy.data.filepath)
    
    # If the blend file hasn't been saved, use the current directory
    if not blend_dir:
        blend_dir = os.getcwd()
        
    output_dir = os.path.join(blend_dir, "output")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    return output_dir


def backup_existing_file(filepath):
    """Create a backup of an existing file by renaming it with a timestamp."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, ext = os.path.splitext(filepath)
        backup_path = f"{filename}_{timestamp}{ext}"
        shutil.move(filepath, backup_path)
        print(f"Existing file backed up to: {backup_path}")


def main():
    """Main function to run the script."""
    start_time = time.time()
    
    # Setup
    collection = setup_environment()
    create_city_scene(collection)
    setup_camera_and_lighting()
    setup_render_settings()
    
    # Prepare output directory
    output_dir = ensure_output_directory()
    output_file = os.path.join(output_dir, "night_city.png")
    
    # Backup existing file if any
    backup_existing_file(output_file)
    
    # Set output path
    bpy.context.scene.render.filepath = output_file
    
    # Render
    bpy.ops.render.render(write_still=True)
    
    end_time = time.time()
    print(f"Script completed in {end_time - start_time:.2f} seconds")
    print(f"Render saved to: {output_file}")


if __name__ == "__main__":
    main()