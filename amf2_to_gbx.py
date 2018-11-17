from reclaimer.hek.defs.mod2 import mod2_def
from defs.amf import amf_def
from reclaimer.model.stripify import Stripifier
import sys
import copy
import time
import math
mod2_ext = ".gbxmodel"
amf_ext = ".amf"
   

MAX_STRIP_LEN = 32763 * 3
def TrianglesToStrips(triangles_list):
    stripifier = Stripifier()
    stripifier.load_mesh(triangles_list, True)
    stripifier.make_strips()
    stripifier.link_strips()

    strips = stripifier.all_strips.get(0)
    tri_strip = strips[0]
    
    if len(tri_strip) > MAX_STRIP_LEN:
        return (
            ("Too many triangles in this part. Max triangles"
             "per part is %s.\nThis part is %s after"
             "linking all strips.") % (MAX_STRIP_LEN, len(tri_strip)), )

    return list(tri_strip)
    
def CalcVertBiNormsAndTangents(gbx_verts, triangles):
    verts = gbx_verts
    vert_ct = len(verts)

    v_indices = (0, 1, 2)
    binormals = [[0, 0, 0, 0] for i in range(vert_ct)]
    tangents  = [[0, 0, 0, 0] for i in range(vert_ct)]
    for tri in triangles:
        for tri_i in range(3):
            v_i = tri[tri_i]
            if v_i >= vert_ct:
                continue

            try:
                v0 = verts[tri[tri_i]]
                v1 = verts[tri[(tri_i + 1) % 3]]
                v2 = verts[tri[(tri_i + 2) % 3]]
            except IndexError:
                print(len(verts), tri)
            return
            b = binormals[v_i]
            t = tangents[v_i]

            x0 = v1.position_x - v0.position_x;
            x1 = v2.position_x - v0.position_x;
            y0 = v1.position_y - v0.position_y;
            y1 = v2.position_y - v0.position_y;
            z0 = v1.position_z - v0.position_z;
            z1 = v2.position_z - v0.position_z;


            s0 = v1.u - v0.u;
            s1 = v2.u - v0.u;
            t0 = v1.v - v0.v;
            t1 = v2.v - v0.v;
            
            r = s0 * t1 - s1 * t0
            if r == 0:
                continue

            r = 1 / r

            bi = -(s0 * x1 - s1 * x0) * r
            bj = -(s0 * y1 - s1 * y0) * r
            bk = -(s0 * z1 - s1 * z0) * r
            b_len = math.sqrt(bi**2 + bj**2 + bk**2)

            ti = (t1 * x0 - t0 * x1) * r
            tj = (t1 * y0 - t0 * y1) * r
            tk = (t1 * z0 - t0 * z1) * r
            t_len = math.sqrt(ti**2 + tj**2 + tk**2)

            if b_len:
                b[0] += bi / b_len
                b[1] += bj / b_len
                b[2] += bk / b_len
                b[3] += 1

            if t_len:
                t[0] += ti / t_len
                t[1] += tj / t_len
                t[2] += tk / t_len
                t[3] += 1

    for i in range(vert_ct):
        vert = verts[i]
        ni = vert.normal_i
        nj = vert.normal_j
        nk = vert.normal_k
        b = binormals[i]
        t = tangents[i]

        if b[3]:
            vert.binormal_i = b[0] / b[3]
            vert.binormal_j = b[1] / b[3]
            vert.binormal_k = b[2] / b[3]

        if t[3]:
            vert.tangent_i = t[0] / t[3]
            vert.tangent_j = t[1] / t[3]
            vert.tangent_k = t[2] / t[3]

    
    
def AmfToMod2(amf_model, do_output):
    gbx_model = mod2_def.build()
    target = gbx_model.data.tagdata
    source = amf_model.data
    
    target.base_map_u_scale = 1.0
    target.base_map_v_scale = 1.0
    
    node_translations = []
    
    t_nodes = target.nodes.STEPTREE
    s_nodes = source.nodes_header.STEPTREE
    if len(s_nodes) > 62:
        print("Warning, node count is over the max supported amount. Supported range: 1-62. Nodecount is: %d"
                % len(s_nodes))
    for s_node in s_nodes:
        t_nodes.append()
        t_node = t_nodes[-1]
        
        if len(s_node.name) > 31:
            t_node.name = s_node.name[0:31]
            print("Warning: The name of node #%d : %s is longer than 31 characters, got: %d" 
                  % (len(t_nodes), s_node.name, len(s_node.name)))
            print("Cutting it short to:", t_node.name)
        else:
            t_node.name = s_node.name
        
        t_node.next_sibling_node    = s_node.sibling_index
        t_node.first_child_node     = s_node.child_index
        t_node.parent_node          = s_node.parent_index
        t_node.translation[0]       = s_node.position[0] / 100
        t_node.translation[1]       = s_node.position[1] / 100
        t_node.translation[2]       = s_node.position[2] / 100
        t_node.rotation             = s_node.orientation
        t_node.distance_from_parent = math.sqrt(t_node.translation[0]**2+t_node.translation[1]**2+t_node.translation[2]**2)
        
    
    target.superhigh_lod_nodes = len(t_nodes)
    target.high_lod_nodes      = len(t_nodes)
    target.medium_lod_nodes    = len(t_nodes)
    target.low_lod_nodes       = len(t_nodes)
    target.superlow_lod_nodes  = len(t_nodes)
    
    t_markers = target.markers.STEPTREE
    s_markers = source.markers_header.STEPTREE
    for s_marker in s_markers:
        t_markers.append()
        t_marker = t_markers[-1]
        
        t_instances = t_marker.marker_instances.STEPTREE
        s_instances = s_marker.marker_instances.STEPTREE
        if len(s_marker.name) > 31:
            t_marker.name = s_marker.name[0:31]
            print("Warning: The name of node #%d : %s is longer than 31 characters, got: %d." 
                  % (len(t_markers), s_marker.name, len(s_marker.name)))
            print("Cutting it short to:", t_marker.name)
        else:
            t_marker.name = s_marker.name
        
        for s_instance in s_instances:
            t_instances.append()
            t_instances[-1][0:3] = s_instance[0:3]
            t_instances[-1].translation[0] = s_instance.position[0] / 100
            t_instances[-1].translation[1] = s_instance.position[1] / 100
            t_instances[-1].translation[2] = s_instance.position[2] / 100
            t_instances[-1][4:7] = s_instance[4:7]
            
    
    
    t_regions = target.regions.STEPTREE
    s_regions = source.regions_header.STEPTREE
    t_geometries = target.geometries.STEPTREE
    if len(s_regions) > 8:
        print("Too many regions, max: 8, got: %s." % len(s_regions))
        
    for s_region in s_regions:
        t_regions.append()
        t_region = t_regions[-1]
        
        if len(s_region.name) > 31:
            t_region.name = s_region.name[0:31]
            print("Warning: The name of node #%d : %s is longer than 31 characters, got: %d." 
                  % (len(t_regions), s_region.name, len(s_region.name)))
            print("Cutting it short to:", t_region.name)
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
            
            if len(perm_name) > 31:
                t_permutation.name = perm_name[0:31]
                print("Warning: The name of permutation #%d : %s in region: #%d : %s is longer than 31 characters, got: %d." 
                      % (len(t_permutations), perm_name, len(t_regions), s_region.name, len(perm_name)))
                print("Cutting it short to:", t_permutation.name)
            else:
                t_permutation.name = perm_name
            
            # set superlow-superhigh geometry block indices
            t_permutation[2:7] = [len(t_geometries)] * 5
            
            t_geometries.append()
            t_geometry = t_geometries[-1]
            
            t_parts = t_geometry.parts.STEPTREE
            #print(s_permutation.vertices_header)
            bounds = None
            if s_permutation.format_info.compression_format != 0:
                bounds     = s_permutation.vertices_header.bounds
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
                    #triangles[-1].extend(s_tris[i][0:2])
                    #print(s_tris[i])
                    used_vert_list[triangles[-1][0]] = True
                    used_vert_list[triangles[-1][1]] = True
                    used_vert_list[triangles[-1][2]] = True
                
                # Get all vertices that are used by these triangles shader
                vert_translation_list = [0] * len(used_vert_list)
                verts = []
                for i in range(len(used_vert_list)):
                    if used_vert_list[i] == True:
                        verts.append(s_verts[i])
                        #print(s_verts[i])
                    vert_translation_list[i] = len(verts)-1
                #print(s_verts)
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
                        t_vert.v = s_vert.data.v
                    else:
                        bounds = s_permutation.vertices_header.bounds
                        t_vert.position_x = ((s_vert.data.position.x / 32767) * (bounds.x.upper - bounds.x.lower) + bounds.x.lower) / 100
                        t_vert.position_y = ((s_vert.data.position.y / 32767) * (bounds.y.upper - bounds.y.lower) + bounds.y.lower) / 100
                        t_vert.position_z = ((s_vert.data.position.z / 32767) * (bounds.z.upper - bounds.z.lower) + bounds.z.lower) / 100
                        
                        t_vert.normal_i = s_vert.data.normal.i / 1023
                        t_vert.normal_j = s_vert.data.normal.j / 1023
                        t_vert.normal_k = s_vert.data.normal.k / 511
                        
                        t_vert.u = (s_vert.data.u / 32767) * (bounds.u.upper - bounds.u.lower) + bounds.u.lower
                        t_vert.v = (s_vert.data.v / 32767) * (bounds.v.upper - bounds.v.lower) + bounds.v.lower
                    
                    if vertex_format == 0:
                        t_vert.node_0_index = s_permutation.node_index
                        t_vert.node_0_weight = 1.0
                        
                    elif vertex_format == 1:
                        t_vert.node_0_index = s_vert.node_indices[0]
                        if s_vert.node_indices[1] != 255:
                            t_vert.node_1_index = s_vert.node_indices[1]
                            t_vert.node_0_weight = 0.5
                            t_vert.node_1_weight = 0.5
                        else:
                            t_vert.node_0_weight = 1.0
                            
                    elif vertex_format == 2:
                        index_count = 1
                        if   indices[1] == 255: index_count = 1
                        elif indices[2] == 255: index_count = 2
                        elif indices[3] == 255: index_count = 3
                        else: index_count = 4
                        
                        # Don't talk to me about this whole vertex weighing and node index logic. Just don't.
                        if index_count == 1:
                            t_vert.node_0_index = s_vert.node_indices[0]
                            t_vert.node_0_weight = 1.0
                        elif index_count == 2:
                            t_vert.node_0_index = s_vert.node_indices[0]
                            t_vert.node_1_index = s_vert.node_indices[1]
                            t_vert.node_0_weight = s_vert.weights[0]
                            t_vert.node_1_weight = s_vert.weights[1]
                        else:
                            # If there is more than 2 node influences we want to use the ones that will most likely look the best
                            unique_weights = list(set(s_vert.data.vert_indices))
                            # If there is multiple nodes with the same weight we might prefer them
                            if len(unique_weights) < len(s_vert.data.vert_indices):
                                occurence_weight = [0, 0.0, [] ] * len(unique_weights)
                                # Count up the total weight of the equally weighed nodes
                                for i in range(len(occurence_weight)):
                                    for j in range(index_count):
                                        if unique_weights[i] == s_vert.weights[j]:
                                            unique_weights[i][0] += 1
                                            unique_weights[i][2].append(s_vert.data.vert_indices[j])
                                    unique_weights[i][1]  = unique_weights[i][0] * unique_weights[i]
                                # Find the equally weighed nodes with the highest total weight
                                highest = [0.0, [] ]
                                second_highest  = [0.0, [] ]
                                for i in range(len(occurence_weight)):
                                    if occurence_weight[i][1] > highest[1]:
                                        highest        = [occurence_weight[i][1], occurence_weight[i][2]]
                                    if occurence_weight[i][1] > second_highest[1] and s_vert.weights[i] < highest[1]:
                                        second_highest = [occurence_weight[i][1], occurence_weight[i][2]]
                                # If the highest equally weighed nodes are a pair of two, just use them.
                                if len(highest[1]) == 2:
                                    t_vert.node_0_index = s_vert.node_indices.vert_indices[highest[1][0]]
                                    t_vert.node_1_index = s_vert.node_indices.vert_indices[highest[1][1]]
                                    t_vert.node_0_weight = 0.5
                                    t_vert.node_1_weight = 0.5
                                # If the highest equally weighed nodes come in a group higher than two,
                                # prefer the ones that share the same parent.
                                elif len(highest[1]) > 2:
                                    parents           = [0] * len(highest[1])
                                    for i in range(len(highest[1])):
                                        parents[i] = t_nodes[highest[1][i]].parent_node
                                        
                                    unique_parents = list(set(parents))
                                    parent_occurances = [0, []] * len(highest[1])
                                    
                                    for i in range(len(unique_parents)):
                                        for j in range(parents):
                                            if unique_parents[i] == parents[j]:
                                                parent_occurances[i][0] += 1
                                                parent_occurances[i][1].append(s_vert.node_indices.vert_indices[j])
                                    highest = [0, []]
                                    for i in range(len(parent_occurances)):
                                        if parent_occurances[i][0] > highest[0]:
                                            highest[0] = parent_occurances[i][0]
                                            highest[1] = parent_occurances[i][1]
                                            
                                    # However many nodes with equal parents there may be at this point, 
                                    # we always want the first and last. As this anecdotally (sigh) seems to be the best solution.
                                    t_vert.node_0_index = s_vert.node_indices.vert_indices[highest[1][0]]
                                    t_vert.node_1_index = s_vert.node_indices.vert_indices[highest[1][-1]]
                                    t_vert.node_0_weight = 0.5
                                    t_vert.node_1_weight = 0.5
                                # If a single node weighs more than any other nodes combined just take that one and the next highest
                                else:
                                    t_vert.node_0_index = s_vert.node_indices.vert_indices[highest[1][0]]
                                    t_vert.node_1_index = s_vert.node_indices.vert_indices[second_highest[1][0]]
                                    t_vert.node_0_weight = s_vert.weights.vert_indices[highest[0]]
                                    t_vert.node_1_weight = s_vert.weights.vert_indices[second_highest[0]]
                            
                            # If there is no nodes with equal weights pick the two highest weight ones.
                            else:
                                highest = [0, 0.0]
                                second_highest  = [0, 0.0]
                                
                                for i in range(index_count):
                                    if s_vert.weights.vert_weights[i] > highest[1]:
                                        highest        = [i, s_vert.weights.vert_weights[i]]
                                    if s_vert.weights.vert_weights[i] > second_highest[1] and s_vert.weights.vert_weights[i] < highest[1]:
                                        second_highest = [i, s_vert.weights.vert_weights[i]]
                                        
                                t_vert.node_0_index = s_vert.node_indices.vert_indices[highest[0]]
                                t_vert.node_1_index = s_vert.node_indices.vert_indices[second_highest[0]]
                                t_vert.node_0_weight = highest[1]
                                t_vert.node_1_weight = second_highest[1]
                                
                            # Fix the weights up so they add up to 1.0
                            total_weight = t_vert.node_0_weight + t_vert.node_1_weight
                            t_vert.node_0_weight /= total_weight
                            t_vert.node_1_weight /= total_weight
                    
                # Calculate the Binormals and Tangents of each vert
                CalcVertBiNormsAndTangents(t_verts, triangles)
                
                ## Convert triangles to strips and add them to the GBX Model Part
                # Translate the triangle vert ids to match the correct verts in the Part
                for triangle in triangles:
                    triangle[0] = vert_translation_list[triangle[0]]
                    triangle[1] = vert_translation_list[triangle[1]]
                    triangle[2] = vert_translation_list[triangle[2]]
                #print(triangles)
                triangle_strip = TrianglesToStrips(triangles)
                
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

                # Calculate the centroid translation by averaging all vertices!
                t_part.centroid_translation[:] = [0.0,0.0,0.0]
                for v in t_verts:
                    for c in range(3):
                        #First 3 indices in a vertex are the translation.
                        t_part.centroid_translation[c] += v[c]
                for c in range(3):
                    t_part.centroid_translation[c] /= len(t_verts)
            
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
        
    return gbx_model
    
#Only run this if the script is ran directly
if __name__ == '__main__':
    from argparse import ArgumentParser
    
    #Initialise startup arguments
    parser = ArgumentParser(description='Converter for AMF models to GBX models.')
    parser.add_argument('amf', metavar='amf', type=str,
                        help='The AMF file we want to convert to a GBX model.')
    parser.add_argument('output', metavar='output', type=str,
                        help='The GBX model we want to save to.')
    args = parser.parse_args()
    
    from shared.SharedFunctions import GetAbsFilepath
    amf_path = GetAbsFilepath(args.amf, amf_ext)

    print("\nLoading AMF model " + amf_path + "...", end='')
    sys.stdout.flush()
    amf = amf_def.build(filepath=(amf_path + amf_ext))
    print("done\n")
    print("Format version:", amf.data.version)
    sys.stdout.flush()

    gbx_model = AmfToMod2(amf, True)
    
    print("Saving GBX model tag...", end='')
    sys.stdout.flush()
    gbx_model.serialize(backup=True, temp=False, filepath=(args.output + mod2_ext))
    print("finished\n")
