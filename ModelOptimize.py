from reclaimer.hek.defs.mod2 import mod2_def
from reclaimer.hek.defs.mod2 import part as part_desc
from supyr_struct.defs.block_def import BlockDef
part_def = BlockDef(part_desc, endian=">")
import sys
import copy
import time
mod2_ext = ".gbxmodel"

# Returns a list of indices for each shader. If there is more than one entry for the same shader
# the list entries corresponding to the duplicates will contain the index of the first occurrence.
def ListShaderIds(shaders_block):
    shaders = shaders_block.STEPTREE
    shader_count = shaders_block.size
    
    shader_ids = [0] * shader_count #preallocate list
    for i in range(shader_count):
        shader_ids[i] = i
        for j in range(i):
            if (shaders[i].shader.filepath == shaders[j].shader.filepath 
            and shaders[i].shader.tag_class == shaders[j].shader.tag_class):
                shader_ids[i] = j
                break

    return shader_ids

    
# Returns a condensed shader block and a list for use when translating 
# the shader indices in the tag to match the new block
def BuildCondensedShaderBlock(shaders_block):
    shaders = shaders_block.STEPTREE
    shader_ids = ListShaderIds(shaders_block)
    condensed_shader_ids = list(set(shader_ids))

    new_shaders = []
    for condensed_shader_id in condensed_shader_ids:
        new_shaders.append(shaders[condensed_shader_id])
    
    new_shader_ids = [0] * len(shader_ids)
    for i in range(len(shader_ids)):
        for j in range(len(condensed_shader_ids)):
            if shader_ids[i] == condensed_shader_ids[j]:
                new_shader_ids[i] = j
                break
    
    return new_shaders, new_shader_ids

    
# Uses the translation_list to determine which old id corresponds to which new id.
# Edits the given geometries_block directly. 
def TranslateGeometryPartShaderIds(geometries_block, translation_list):
    geometries = geometries_block.STEPTREE
    
    for geometry in geometries:
        parts = geometry.parts.STEPTREE
        for part in parts:
            part.shader_index = translation_list[part.shader_index]


# Uses the translation_list to determine which old node id corresponds to which new node id.
# Edits the given part_steptree_entry directly. 
def TranslatePartNodeIds(part_steptree_entry, translation_list):
    verts = part_steptree_entry.uncompressed_vertices.STEPTREE
    
    for vert in verts:
        vert.node_0_index = translation_list[vert.node_0_index]
        vert.node_1_index = translation_list[vert.node_1_index]
        if (vert.node_1_weight == 0):
            vert.node_1_index = 0
    
    part_steptree_entry.compressed_vertices.STEPTREE.clear()


    
# Takes a geometry and sorts all of it's parts into subgroups based on what shader they use.
def GroupGeometryPartsByShader(geometry, shaders_block):
    shader_count = len(shaders_block.STEPTREE)
    
    groups = []
    parts = geometry.parts.STEPTREE
    for i in range(shader_count):
        current_list = []
        for part in parts:
            if part.shader_index == i:
                current_list.append(part)
                
        groups.append(current_list)
    
    return groups
    
    
    
# Takes a list of geometry parts, merges all their geometry, and returns the resulting part.
def CombinePartsFromList(list):
    current_offset = 0
    
    shader_id = list[0].shader_index
    vert_counts = []
    centroids = []
    
    combined_verts = []
    triangle_strip_chain = []
    
    # loop through all parts in the list
    for i in range(len(list)):
        triangles = list[i].triangles.STEPTREE
        verts = list[i].uncompressed_vertices.STEPTREE
        centroid = list[i].centroid_translation
        
        current_strip = []
        # convert the 'triangles' to individual triangle strip points
        for triangle in triangles:
            current_strip.extend((triangle.v0_index + current_offset,
                                  triangle.v1_index + current_offset,
                                  triangle.v2_index + current_offset))
        # remove -1s at the end, but check if < current_offset as we added that to them
        while current_strip and current_strip[-1] < current_offset:
            current_strip.pop(-1)
        # if the number of triangles in this strip is uneven we need to copy the last vert
        if len(current_strip)%2 == 1 and i < len(list)-1:
            current_strip.append(current_strip[-1])
        # if the strip isn't the first copy the first vert to properly connect it to the one before
        if i != 0:
            current_strip.insert(0, current_strip[0])
        # if the strip is the last strip don't add a copy of the last strip point
        if i < len(list)-1:
            current_strip.append(current_strip[-1])

        # add the current chain to the main chain
        triangle_strip_chain.extend(current_strip)
        # add the verts of this part to the combined set of verts
        combined_verts.extend(verts)
        # add the current vert count to the offset
        current_offset += len(verts)
        # save vert count for centroid averaging
        vert_counts.append(len(verts))
        # save centroid for averaging
        centroids.append(centroid)
    
    #create the new part we'll be writing to
    new_part = part_def.build()
    # set the right shader id
    new_part.shader_index = shader_id
    
    # get a weighted average of all centroids
    for centroid,vert_count in zip(centroids,vert_counts):
        new_part.centroid_translation.x += centroid.x * vert_count
        new_part.centroid_translation.y += centroid.y * vert_count
        new_part.centroid_translation.z += centroid.z * vert_count
    new_part.centroid_translation.x /= sum(vert_counts)
    new_part.centroid_translation.y /= sum(vert_counts)
    new_part.centroid_translation.z /= sum(vert_counts)
    
    # assign our set of verts to the uncompressed vertices block
    new_part.uncompressed_vertices.STEPTREE[:] = combined_verts
    
    # the triangles struct we want to fit the strip into 
    # requires the left over spots to be filled with -1s.
    # we mod 3 a second time because we don't want the 
    # struct to end in 3 -1s.
    number_of_required_extra_neg_ones = (3 - len(triangle_strip_chain)%3)%3
    for i in range(number_of_required_extra_neg_ones):
        triangle_strip_chain.append(-1)
        
    # convert the strip into sets of 3 strip verts per 'triangle'
    tris = new_part.triangles.STEPTREE
    for i in range(0, len(triangle_strip_chain), 3):
        tris.append()
        tris[-1][:] = triangle_strip_chain[i : i+3]
    
    
    return new_part
    
    
    
# Takes groups of parts sorted by shader, condenses them by shader, and returns the resulting parts.
def BuildPartList(groups):
    
    parts = []
    for group in groups:
        if (len(group) > 0):
            parts.append(CombinePartsFromList(group))
    return parts
            
            
# Takes a list of vertices and makes a new list that has all duplicates remove and returns it,
# and a translation list for fixing the triangles block.
def BuildCondensedVertexBlock(vertices_block):
    verts = vertices_block.STEPTREE

    new_verts = []
    verts_lists_by_quick_ids = dict()
    translation_list = []

    for i in range(len(verts)):
        vert = verts[i]
        quick_id = (vert.position_x, vert.position_y, vert.position_z)
        found = False
        if quick_id in verts_lists_by_quick_ids:
            for dict_vert, index in verts_lists_by_quick_ids[quick_id]:
                if vert == dict_vert:
                    found = True
                    translation_list.append(index)
                    break
        
        if not found:
            verts_lists_by_quick_ids.setdefault(quick_id, []).append((vert, len(new_verts)))
            translation_list.append(len(new_verts))
            new_verts.append(vert)
            
    return new_verts, translation_list




#########################################################################



# Gets rid of all duplicate shaders without breaking shader indices.
def ModelCondenseShaders(model_tag):
    model = model_tag.data.tagdata

    new_shaders, translation_list = BuildCondensedShaderBlock(model.shaders)
    model.shaders.STEPTREE[:] = new_shaders
    
    TranslateGeometryPartShaderIds(model.geometries, translation_list)
    
    
    
# Removes all local nodes by turning the setting off in the geometry parts
# and translating their node indices to absolute.
def ModelRemoveLocalNodes(model_tag):
    model = model_tag.data.tagdata
    geometries = model.geometries.STEPTREE
    
    for geometry in geometries:
        parts = geometry.parts.STEPTREE
        for part in parts:
            if part.flags.ZONER:
                TranslatePartNodeIds(part, part.local_nodes)
                part.local_nodes.clear()
                part.flags.ZONER = False
                
    model.flags.parts_have_local_nodes = False

    
    
# Reduces the number of drawcalls per region by merging geometry parts that use the same shader.
def ModelMergeGeometryPartsWithIdenticalShaderIds(model_tag):
    model = model_tag.data.tagdata
    geometries = model.geometries.STEPTREE
    shaders = model.shaders
    
    original_part_count = 0
    new_part_count = 0
    
    for geometry in geometries:
        original_part_count += len(geometry.parts.STEPTREE)
        geometry.parts.STEPTREE[:] = BuildPartList(GroupGeometryPartsByShader(geometry, shaders))
        new_part_count += len(geometry.parts.STEPTREE)
        
    return original_part_count, new_part_count
        
        
        
# For each geometry part gets rid of all duplicate vertices.
def ModelRemoveDuplicateVertices(model_tag):
    model = model_tag.data.tagdata
    geometries = model.geometries.STEPTREE
    
    original_vert_count = 0
    new_vert_count = 0
    
    for geometry in geometries:
        parts = geometry.parts.STEPTREE
        for part in parts:
            original_vert_count += len(part.uncompressed_vertices.STEPTREE)
            part.compressed_vertices.clear()
            new_verts, translation_list = BuildCondensedVertexBlock(part.uncompressed_vertices)
            part.uncompressed_vertices.STEPTREE[:] = new_verts
            
            triangles = part.triangles.STEPTREE
            for triangle in triangles:
                if triangle.v0_index != -1:triangle.v0_index = translation_list[triangle.v0_index]
                if triangle.v1_index != -1:triangle.v1_index = translation_list[triangle.v1_index]
                if triangle.v2_index != -1:triangle.v2_index = translation_list[triangle.v2_index]
            new_vert_count += len(part.uncompressed_vertices.STEPTREE)
    
    return original_vert_count, new_vert_count

    
# Controls the calling of all the functions. Use this to ensure that all 
# required steps are done for the tasks you want executed.
def ModelOptimize(model_tag, do_output, condense_shaders, remove_local_nodes, condense_parts, condense_verts):
    model = model_tag.data.tagdata
    # setup
    if condense_parts:
        condense_shaders = True
        remove_local_nodes = True
    
    # actual execution
    if condense_shaders: 
        if do_output:
            start = time.time()
            print("Condensing shaders block...", end='')
            sys.stdout.flush()
            old_shaders_size = model.shaders.size
        ModelCondenseShaders(model_tag)
        if do_output:
            end = time.time()
            print("done", " - Reduced shader count from ", old_shaders_size, " to ", model.shaders.size, ".", sep='')
            print("    Took", end-start, "seconds\n")
        
    if remove_local_nodes:
        if do_output:
            start = time.time()
            print("Removing Local Nodes...", end='')
            sys.stdout.flush()
        ModelRemoveLocalNodes(model_tag)
        if do_output:
            end = time.time()
            print("done\n    Took", end-start, "seconds\n")
    
    if condense_parts:
        if do_output:
            start = time.time()
            print("Condensing Geometry Parts...", end='')
            sys.stdout.flush()
        part_counts = ModelMergeGeometryPartsWithIdenticalShaderIds(model_tag)
        if do_output:
            end = time.time()
            print("done", " - Reduced total part count from ", part_counts[0], " to ", part_counts[1],"\n    Took ", end-start, " seconds\n", sep='')
        
    if condense_verts:
        if do_output:
            start = time.time()
            print("Condensing Duplicate Vertices...", end='')
            sys.stdout.flush()
        vert_counts = ModelRemoveDuplicateVertices(model_tag)
        if do_output:
            end = time.time()
            print("done", " - Reduced total vertex count from ", vert_counts[0], " to ", vert_counts[1],"\n    Took ", end-start, " seconds\n", sep='')
        
    
    
    
#Only run this if the script is ran directly
if __name__ == '__main__':
    from argparse import ArgumentParser
    
    #Initialise startup arguments
    parser = ArgumentParser(description='Halo Gbxmodel optimizer. Made to optimize the model for render speed.')
    parser.add_argument('-s', '--remove-duplicate-shaders', dest='remove_shader_dupes', action='store_const',
                        const=True, default=False,
                        help='Removes duplicate shaders in the model tag without breaking indices.')
    parser.add_argument('-a', '--remove-local-nodes', dest='remove_local_nodes', action='store_const',
                        const=True, default=False,
                        help='Rereferences all local nodes to use absolute nodes.')
    parser.add_argument('-p', '--condense-geometry-parts', dest='condense_geometry_parts', action='store_const',
                        const=True, default=False,
                        help='For each geometry combines all parts that use the same shader. (Automatically enables --remove-duplicate-shaders and --remove-local-nodes)')
    parser.add_argument('-v', '--remove-duplicate-vertices', dest='remove_duplicate_vertices', action='store_const',
                        const=True, default=False,
                        help='For each geometry part removes all duplicate vertices.')
    parser.add_argument('model_tag', metavar='model_tag', type=str,
                        help='The tag we want to operate on.')
    args = parser.parse_args()
    
    from shared.SharedFunctions import GetAbsFilepath
    model_tag_path = GetAbsFilepath(args.model_tag, mod2_ext)

    print("\nLoading model " + model_tag_path + "...", end='')
    sys.stdout.flush()
    model_tag = mod2_def.build(filepath=(model_tag_path + mod2_ext))
    print("done\n")

    ModelOptimize(model_tag, True, args.remove_shader_dupes, args.remove_local_nodes, args.condense_geometry_parts, args.remove_duplicate_vertices)
    
    print("Saving model tag...", end='')
    sys.stdout.flush()
    model_tag.serialize(backup=True, temp=False)
    print("finished\n")
