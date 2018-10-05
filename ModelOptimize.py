from reclaimer.hek.defs.mod2 import mod2_def
import copy

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
            if (shader_ids[i] == condensed_shader_ids[j]):
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
            
            
      
      
def TranslatePartNodeIds(part_steptree_entry, translation_list):
    verts = part_steptree_entry.uncompressed_vertices.STEPTREE
    
    for vert in verts:
        vert.node_0_index = translation_list[vert.node_0_index]
        vert.node_1_index = translation_list[vert.node_1_index]
        if (vert.node_1_weight == 0):
            vert.node_1_index = 0
    
    part_steptree_entry.compressed_vertices.STEPTREE.clear()


    
    
def ModelCondenseShaders(model_tag):
    model = model_tag.data.tagdata

    new_shaders = BuildCondensedShaderBlock(model.shaders)
    model.shaders.STEPTREE[:] = new_shaders[0]
    
    TranslateGeometryPartShaderIds(model.geometries, new_shaders[1])
    
    
    

def ModelRemoveLocalNodes(model_tag):
    model = model_tag.data.tagdata
    geometries = model.geometries.STEPTREE
    
    for geometry in geometries:
        parts = geometry.parts.STEPTREE
        for part in parts:
            if (part.flags.ZONER):
                TranslatePartNodeIds(part, part.local_nodes)
                part.local_nodes.clear()
                part.flags.ZONER = False
                
    model.flags.parts_have_local_nodes = False
                
# Controls the calling of all the functions. Use this to ensure that all 
# required steps are done for the task you want executed.
def ModelOptimize(model_tag, do_output, condense_shaders, remove_local_nodes):
    model = model_tag.data.tagdata
    
    if condense_shaders: 
        if do_output:
            print("Condensing shaders block...", end='')
            old_shaders_size = model.shaders.size
        ModelCondenseShaders(model_tag)
        if do_output:print("done", " - Reduced shader count from ", old_shaders_size, " to ", model.shaders.size, ".\n", sep='')
        
    if remove_local_nodes:
        if do_output:print("Removing Local Nodes...", end='')
        ModelRemoveLocalNodes(model_tag)
        if do_output:print("done\n")
    

    
#Only run this if the script is ran directly
if __name__ == '__main__':
    from argparse import ArgumentParser
    
    #Initialise startup arguments
    parser = ArgumentParser(description='Halo Gbxmodel optimizer. Made to optimize the model for render speed. [Does not remove triangles.]')
    parser.add_argument('-s', '--remove-duplicate-shaders', dest='remove_shader_dupes', action='store_const',
                        const=True, default=False,
                        help='Removes duplicate shaders in the model tag without breaking indices.')
    parser.add_argument('-a', '--remove-local-nodes', dest='remove_local_nodes', action='store_const',
                        const=True, default=False,
                        help='Rereferences all local nodes to use absolute nodes.')
    parser.add_argument('model_tag', metavar='model_tag', type=str,
                        help='The tag we want to operate on.')
    args = parser.parse_args()
    
    from shared.SharedFunctions import GetAbsFilepath
    model_tag_path = GetAbsFilepath(args.model_tag, mod2_ext)

    print("\nLoading model " + model_tag_path + "...", end='')
    model_tag = mod2_def.build(filepath=(model_tag_path + mod2_ext))
    print("done\n")

    ModelOptimize(model_tag, True, args.remove_shader_dupes, args.remove_local_nodes)
    
    print("Saving model tag...", end='')
    model_tag.serialize(backup=True, temp=False)
    print("finished\n")
