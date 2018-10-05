from reclaimer.hek.defs.mod2 import mod2_def
import os
import sys
import copy
from supyr_struct.defs.block_def import BlockDef
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
    for i in range(len(condensed_shader_ids)):
        new_shaders.append(shaders[condensed_shader_ids[i]])
    
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
    for i in range(len(geometries)):
        parts = geometries[i].parts.STEPTREE
        for j in range(len(parts)):
            parts[j].shader_index = translation_list[parts[j].shader_index]
            

            
def TranslatePartNodeIds(part_steptree_entry, translation_list):
    part_steptree_entry.compressed_vertices.STEPTREE.clear()
    verts = part_steptree_entry.uncompressed_vertices.STEPTREE
    part_steptree_entry.flags.ZONER = False
    for k in range(len(verts)):
        verts[k].node_0_index = translation_list[verts[k].node_0_index]
        verts[k].node_1_index = translation_list[verts[k].node_1_index]
        if (verts[k].node_1_weight == 0):
            verts[k].node_1_index = 0
    


def ModelCondenseShaders(model_tag):
    print("Condensing shaders block...")
    model = model_tag.data.tagdata
    
    new_shaders = BuildCondensedShaderBlock(model.shaders)
    model.shaders.STEPTREE.clear()
    model.shaders.STEPTREE.extend(new_shaders[0])
    
    print("Translating shader indices in geometry parts...")
    TranslateGeometryPartShaderIds(model.geometries, new_shaders[1])
    
    

def ModelRemoveLocalNodes(model_tag):
    model = model_tag.data.tagdata
    if (model.flags.parts_have_local_nodes):
        model.flags.parts_have_local_nodes = False
        print("Removing Local Nodes...")
        geometries = model.geometries.STEPTREE
        for i in range(len(geometries)):
            parts = geometries[i].parts.STEPTREE
            for j in range(len(parts)):
                TranslatePartNodeIds(parts[j], parts[j].local_nodes)
                parts[j].local_nodes.clear()
    else:
        print("Model has no local nodes.")

    


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
                        help='The tag we want to operate on. If no other args are given we just display the information on this tag')
                        
    args = parser.parse_args()

    #Remove any occurences of the file extension in the paths
    model_tag_path = args.model_tag.replace(mod2_ext, "")
    
    #Check if the file exists in both a path relative to the location the script is being executed from
    #and if it can't find it there, look for it as an absolute path
    if (os.path.isfile(os.path.join('./',  model_tag_path + mod2_ext))):
        model_tag_path = os.path.join('./', model_tag_path)
    elif (os.path.isfile(model_tag_path + mod2_ext)):
        model_tag_path = model_tag_path
    else:
        sys.exit("The file " + model_tag_path + mod2_ext + " does not exist.")
    
    print("Loading model tag...")
    model_tag = mod2_def.build(filepath=(model_tag_path + mod2_ext))
    
    if (args.remove_shader_dupes):
        ModelCondenseShaders(model_tag)
    if (args.remove_local_nodes):
        ModelRemoveLocalNodes(model_tag)
    

    model_tag.serialize(backup=True, temp=False)
    print("Finished.")
#end
