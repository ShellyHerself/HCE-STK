# File definitions
from reclaimer.hek.defs.mod2 import mod2_def
from defs.amf import amf_def

import shared.model_functions as fmodel
import shared.struct_functions as fstruct

from shared.classes_3d import Vec3d
from shared.classes_3d import Quaternion

import logging as log

fixup_nodes_names_list = ("fixup", "jiggle")
remove_nodes_names_list = ("pedestal", "aim_pitch", "aim_yaw")
dirty_rig_fix_exclude_list = ("shoulder")



# Use AMF node list to generate a list of which nodes we should ignore when skinning verts.
def GetDirtyRigFixList(amf_nodes):
    log.info("Fetching list of nodes to ignore for dirty rig fix.")
    node_ignore_id = [False] * len(amf_nodes)
    
    for i in range(len(amf_nodes)):
        node = amf_nodes[i]
        if (node.name.endswith(fixup_nodes_names_list)
        and dirty_rig_fix_exclude_list in node.name):
            node_ignore_id[i] = True
            
    return node_ignore_id
    
    
# Takes a set of AMF nodes and returns a list of what each id should
# translate to, and a list of ids for the nodes we should keep.
def GetTransListForHelperStripping(amf_nodes):
    log.info("Fetching list of nodes to strip.")
    
    strip_these = fixup_nodes_names_list + remove_nodes_names_list
    node_id_translation_list = []
    node_leftover_id = []
    
    next_id = 0
    for i in range(len(amf_nodes)):
        node = amf_nodes[i]
        if node.name.endswith(strip_these):
            if not ("wrist" in node.name):
                # Fixups usually just adjust verts around their parents, so we reskin them to their parent nodes.
                node_id_translation_list.setdefault(i, node_id_translation_list[node.parent_index])
            else:
                # Wrists have the hand as their parent in newer halos.
                # But they need to be skinned to the forearm so it looks better in halo 1.
                parent = amf_nodes[node.parent_index]
                node_id_translation_list.setdefault(i, node_id_translation_list[parent.parent_index])
        else:
            # Each node that isn't getting removed gets its own new id starting from 0.
            node_id_translation_list.setdefault(i, next_id)
            node_leftover_id.append(i)
            next_id += 1
            
    return node_id_translation_list, node_leftover_id

    
    
# Main function: Converts AMF into GBX Model.
def AmfToMod2(amf, strip_helpers, dirty_rig_fix):
    gbx = mod2_def.build()
    t   = gbx.data.tagdata #target
    s   = amf.data         #source
    
    log.info("Building nodes block...")
    
    # Node lists
    t_nodes = t.nodes.STEPTREE
    s_nodes = s.nodes_header.STEPTREE
    
    # Vertex weights use ids, so we will build lists for translating and ignoring.
    # We need this because the node setup in the gbx model will be different,
    # which would mean that the ids don't match up.
    node_s_to_t      = [] # list for translating node ids from our s_nodes set to our t_nodes set.
    node_leftover_id = [] # list of ids of nodes from s_nodes we should keep.
    node_ignore_id   = [] # list that determines which node weights the skinning process should ignore.
    
    # Set up our lists appropriately.
    # Get conversion and rig fix lists if applicable. And just create dummy lists if not.
    if strip_helpers:
        node_s_to_t, node_leftover_id = GetTransListForHelperStripping(s_nodes)
    else:
        for i in range(len(s_nodes)):
            node_s_to_t.append(i)
            node_leftover_id.append(i)
            
            
    if dirty_rig_fix:
        node_ignore_id = GetDirtyRigFixList(s_nodes)
    else:
        node_ignore_id = [False] * len(s_nodes)
    
    
    # Build the node list in the target gbx.
    for id in node_leftover_id:
        s_node = s_nodes[id]
        t_nodes.append()
        t_node = t_nodes[-1]
        
        if len(s_node.name) > 31:
            t_node.name = s_node.name[0:31]
            log.warning("Warning: The name of node #%d : %s is longer than 31 characters, got: %d\nCutting it short to: %s" % (len(t_nodes), s_node.name, len(s_node.name), t_node.name))
        else:
            t_node.name = s_node.name
    
        t_node.parent_node          = node_s_to_t[s_node.parent_node]
        trans                       = Vec3d(s_node.translation) / 100
        t_node.translation[:]       = trans[:]
        t_node.rotation[:]          = Quaternion(s_node.rotation).inverse[:]
        t_node.distance_from_parent = trans.magnitude
        
        
    # Fix positions and rotations when stripping helpers.
    if strip_helpers:
        # Get absolute transforms.
        abs_transforms = fmodel.GetAbsNodetransforms(s_nodes)
        # Cut down list to only include the abs transforms for the leftover nodes.
        abs_transforms = fstruct.CreateNewListUsingIds(abs_transforms, node_leftover_id)
        # Fix size and rotation inconsistencies between AMF and GBX.
        for transform in abs_transforms:
            transform[0] = transform[0] / 100
            transform[1] = transform[1].inverse
        # Apply changes.
        t_nodes[:] = SetRelNodetransforms(t_nodes, abs_transforms)[:]
        
        
    # Fix node order to abide by Halo's node sorting rules. Per level, alphabetical.
    t_nodes, translation_list = fmodel.SortNodes(t_nodes)
    # Update translation list to reflect the new order.
    for t in node_s_to_t:
        t = translation_list[t]
        
    
    log.info("Building markers block...")
    
    # Marker lists
    t_markers = t.markers.STEPTREE
    s_markers = s.markers_header.STEPTREE
    
    # Build markers block
    for s_marker in s_markers:
        t_markers.append()
        t_marker = t_markers[-1]
        
        if len(s_marker.name) > 31:
            t_marker.name = s_marker.name[0:31]
            log.warning("Warning: The name of marker #%d : %s is longer than 31 characters, got: %d\nCutting it short to: %s" % (len(t_markers), s_marker.name, len(s_markers.name), t_marker.name))
        else:
            t_marker.name = s_marker.name
            
        t_instances = t_marker.marker_instances.STEPTREE
        s_instances = s_marker.marker_instances.STEPTREE
        
        for s_instance in s_instances:
            t_instances.append()
            t_instance = t_instances[-1]
            
            t_instance[0:3] = s_instance[0:3]
            t_instance.translation[:] = (Vec3d(s_instance.position) / 100)[:]
            t_instance.rotation[:] = Quaternion(s_instance.orientation).inverse[:]
            
            t_instance.node_index = node_s_to_t[t_instance.node_index]
            
    log.info("Building regions and geometries blocks...")
    
    t_regions = target.regions.STEPTREE
    s_regions = source.regions_header.STEPTREE
    
    t_geometries = target.geometries.STEPTREE
    
    for s_region in s_regions:
        t_regions.append()
        t_region = t_regions[-1]
        
        if len(s_region.name) > 31:
            t_region.name = s_region.name[0:31]
            log.warning("Warning: The name of region #%d : %s is longer than 31 characters, got: %d\nCutting it short to: %s" % (len(t_regions), s_region.name, len(s_regions.name), t_region.name))
        else:
            t_region.name = s_region.name
        
        t_permutations = t_region.permutations.STEPTREE
        s_permutations = s_region.permutations_header.STEPTREE
        
        for s_permutation in s_permutations:
            t_permutations.append()
            t_permutation = t_permutations[-1]
            
            perm_name = s_permutation.name
            if t_region.name == "Instances":
                perm_name = perm_name.replace("%", "", 1)
                
            if len(s_permutation.name) > 31:
                t_permutation.name = perm_name[0:31]
                log.warning("Warning: The name of permutation #%d : %s is longer than 31 characters, got: %d\nCutting it short to: %s" % (len(t_permutations), perm_name, len(perm_name), t_permutation.name))
            else:
                t_permutation.name = perm_name
                
            # set superlow-superhigh geometry block indices
            t_permutation[2:7] = [len(t_geometries)] * 5
            
            t_geometries.append()
            t_geometry = t_geometries[-1]
            
            t_parts = t_geometry.parts.STEPTREE
            
            bounds = None
            if s_permutation.format_info.compression_format != 0:
                bounds = s_permutation.vertices_header.bounds
            s_verts    = s_permutation.vertices_header.vertices.vertices
            s_tris     = s_permutation.faces_header.STEPTREE
            s_sections = s_permutation.sections_header.STEPTREE
            
            for s_section in s_sections:
                t_parts.append()
                t_part = t_parts[-1]
                
                t_part.shader_index = s_section.shader_index
                
                # Get all the triangles that use this shader
                used_vert_list = [False] * len(s_verts)
                triangles = []
                for i in range(s_section.starting_face, s_section.starting_face+s_section.face_count):
                    triangles.append(s_tris[i][:])
                    
                    used_vert_list[triangles[-1][0]] = True
                    used_vert_list[triangles[-1][1]] = True
                    used_vert_list[triangles[-1][2]] = True
                    
                # Get all vertices that are used by these triangles shader
                vert_translation_list = [0] * len(used_vert_list)
                verts = []
                for i in range(len(used_vert_list)):
                    if used_vert_list[i] == True:
                        verts.append(s_verts[i])
                    vert_translation_list[i] = len(verts)-1
                    
                ## Get all relevant info from each vert and add it to the GBX Model Part
                t_verts            = t_part.uncompressed_vertices.STEPTREE
                vertex_format      = s_permutation.format_info.vertex_format
                compression_format = s_permutation.format_info.compression_format
                
                for s_vert in verts:
                    t_verts.append()
                    t_vert = t_verts[-1]
                    
                    if compression_format == 0:
                        t_vert[0] = s_vert.data.position[0] / 100
                        t_vert[1] = s_vert.data.position[1] / 100
                        t_vert[2] = s_vert.data.position[2] / 100
                        t_vert[3:6] = s_vert.data.normal[0:3]
                        # binormals and tangents are calculated when all verts are added to the STEPTREE
                        t_vert.u = s_vert.data.u
                        t_vert.v = 1 - s_vert.data.v
                    else:
                        bounds = s_permutation.vertices_header.bounds
                        t_vert.position_x = ((s_vert.data.position.x / 32767) * (bounds.x.upper - bounds.x.lower) + bounds.x.lower) / 100
                        t_vert.position_y = ((s_vert.data.position.y / 32767) * (bounds.y.upper - bounds.y.lower) + bounds.y.lower) / 100
                        t_vert.position_z = ((s_vert.data.position.z / 32767) * (bounds.z.upper - bounds.z.lower) + bounds.z.lower) / 100
                        
                        t_vert.normal_i = s_vert.data.normal.i / 1023
                        t_vert.normal_j = s_vert.data.normal.j / 1023
                        t_vert.normal_k = s_vert.data.normal.k / 511
                        
                        t_vert.u = (s_vert.data.u / 32767) * (bounds.u.upper - bounds.u.lower) + bounds.u.lower
                        t_vert.v = 1 - ((s_vert.data.v / 32767) * (bounds.v.upper - bounds.v.lower) + bounds.v.lower)
                        
                    if vertex_format == 0:
                        t_vert.node_0_index = node_s_to_t[s_permutation.node_index]
                        t_vert.node_0_weight = 1.0
                        
                    elif vertex_format == 1:
                        t_vert.node_0_index = node_s_to_t[s_vert.node_indices[0]]
                        if s_vert.node_indices[1] != 255:
                            if node_s_to_t[s_vert.node_indices[1]] == t_vert.node_0_index:
                                t_vert.node_0_weight = 1.0
                            else:
                                t_vert.node_1_index = node_s_to_t[s_vert.node_indices[1]]
                                t_vert.node_0_weight = 0.5
                                t_vert.node_1_weight = 0.5
                        else:
                            t_vert.node_0_weight = 1.0
                            
                    elif vertex_format == 2:
                        index_count = 1
                        if   s_vert.node_indices[1] == 255: index_count = 1
                        elif s_vert.node_indices[2] == 255: index_count = 2
                        elif s_vert.node_indices[3] == 255: index_count = 3
                        else: index_count = 4
                            
                        # Make a list of all different ids this vert is skinned to, adding up weight of dupes.
                        v_node_ids = []
                        v_weights = []
                        for i in range(index_count):
                            if not node_ignore_id[s_vert.node_indices[i]]:
                                match = None
                                effective_node_id = node_s_to_t[s_vert.node_indices[i]]
                                for i in range(len(v_node_ids)):
                                    if v_node_ids[i] == effective_node_id:
                                        match = i
                                        break
                                if match == None:
                                    v_node_ids.append(effective_node_id)
                                    v_node_weights.append(s_vert.node_weights[i])
                                else:
                                    v_weights[match] += s_vert.node_weights[i]
                                    
                        if not len(v_node_ids) > 1:
                            t_vert.node_0_index = v_node_ids[0]
                            t_vert.node_0_weight = 1.0
                            t_vert.node_1_index = -1
                            t_vert.node_1_weight = 0.0
                        else:
                            # Get two highest weight nodes
                            highest_weight_id = v_weights.index(max(v_weights))
                            t_vert.node_0_index = v_node_ids.pop(highest_weight_id)
                            t_vert.node_0_weight = v_weights.pop(highest_weight_id)
                            highest_weight_id = v_weights.index(max(v_weights))
                            t_vert.node_1_index = v_node_ids.pop(highest_weight_id)
                            t_vert.node_1_weight = v_weights.pop(highest_weight_id)
                            # Normalize the weights
                            total_weight = t_vert.node_0_weight + t_vert.node_1_weight
                            t_vert.node_0_weight /= total_weight
                            t_vert.node_1_weight /= total_weight
                            
                ## Convert triangles to strips and add them to the GBX Model Part
                # Translate the triangle vert ids to match the correct verts in the Part
                for triangle in triangles:
                    triangle[0] = vert_translation_list[triangle[0]]
                    triangle[1] = vert_translation_list[triangle[1]]
                    triangle[2] = vert_translation_list[triangle[2]]
                
                # Calculate the Binormals and Tangents of each vert
                fmodel.CalcVertBiNormsAndTangents(t_verts, triangles)
                
                triangle_strip = fmodel.TrianglesToStrips(triangles)
                
                # The triangle strip needs to be divisible by 3
                needed_padding = (3 - len(triangle_strip) % 3) % 3
                
                # Any unused/padding slots in the triangles array need to have the number -1
                for i in range(needed_padding):
                    triangle_strip.append(-1)
                    
                # Write the strip to the array
                t_tris = t_part.triangles.STEPTREE
                for i in range(0, len(triangle_strip), 3):
                    t_tris.append()
                    t_tris[-1][:] = triangle_strip[i : i+3]
                
                xs = []
                ys = []
                zs = []
                for v in t_verts:
                    xs.append(v[0])
                    ys.append(v[1])
                    zs.append(v[2])
                    
                x_hi = max(xs)
                y_hi = max(ys)
                z_hi = max(zs)
                
                x_lo = min(xs)
                y_lo = min(ys)
                z_lo = min(zs)
                
                t_part.centroid_translation[0] = (x_hi - x_lo) / 2.0 + x_lo
                t_part.centroid_translation[1] = (y_hi - y_lo) / 2.0 + y_lo
                t_part.centroid_translation[2] = (z_hi - z_lo) / 2.0 + z_lo
                
                
                
    log.info("Building shaders block...")
    # Todo, make this less shit or make main process this
    t_shaders = target.shaders.STEPTREE
    s_shaders = source.shaders_header.STEPTREE
    shaders_already_exist = []
    for s_shader in s_shaders:
        t_shaders.append()
        t_shader = t_shaders[-1]
        t_shader.shader.filepath = s_shader.name
        for exists in shaders_already_exist:
            if exists[0][0] == s_shader.name:
                exists[0][1] += 1
        exists = [s_shader.name, 1]
        shaders_already_exist.append(exists)
                    
        
    if len(s_regions) > 8:
        print("Too many regions, max: 8, got: %s.\nYou'll have to fix this manually." % len(s_regions))
    
    return gbx

if __name__ == '__main__':
    from argparse import ArgumentParser
    
    # Initialise startup arguments
    parser = ArgumentParser(description='Converter for AMF models to GBX models.')
    parser.add_argument('-s', '--strip-helpers', dest='strip', action='store_const',
                        const=True, default=False,
                        help='Purges helper bones like fixups, pedestals, jiggle, aim.')
    parser.add_argument('-d', '--dirty-rig_fix', dest='dirty_fix', action='store_const',
                        const=True, default=False,
                        help='Pre-processes the AMF file a little so that some common skinning problems are fixed in the output gbx.')
    parser.add_argument('input_amf', metavar='amf', type=str,
                        help='The AMF file we want to convert to a GBX model.')
    parser.add_argument('output_gbxmodel', metavar='output', type=str,
                        help='The GBX model we want to save to.')
    args = parser.parse_args()
    
    import sys
    log.basicConfig(stream=sys.stdout, level=log.DEBUG)
    
    mod2_ext = ".gbxmodel"
    amf_ext  = ".amf"
    
    from shared.SharedFunctions import GetAbsFilepath
    amf_path = GetAbsFilepath(args.input_amf, amf_ext)

    log.info("Loading AMF model %s" % (amf_path))
    
    amf = amf_def.build(filepath=(amf_path + amf_ext))

    log.info("Format version: %s" % (amf.data.version))

    gbx_model = AmfToMod2(amf, args.strip, args.dirty_fix)
    
    log.info("Saving Gbxmodel tag")
    gbx_model.serialize(backup=True, temp=False, filepath=(args.output_gbxmodel + mod2_ext))
    log.info("finished")
