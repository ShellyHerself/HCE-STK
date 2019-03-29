from reclaimer.model.stripify import Stripifier
from .classes_3d import Vec3d
from .classes_3d import Quaternion
from .classes_3d import Matrix
import shared.struct_functions as fstruct

import copy
import math




MAX_STRIP_LEN = 32763 * 3
def TrianglesToStrips(triangles_list):
    stripifier = Stripifier()
    stripifier.load_mesh(triangles_list, True)
    stripifier.make_strips()
    stripifier.link_strips()

    tri_strip = stripifier.translate_strip(stripifier.all_strips.get(0)[0])

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

    
# Takes a nodes STEPTREE and returns the absolute transformations
# In a list with the structure [absolute_position, absulute_rotation_matrix]
def GetAbsNodetransforms(node_list):
    nodes = node_list
    node_transforms = []
    
    for node in nodes:
        translation = Vec3d(node.translation)
        rotation = Quaternion(node.rotation).to_matrix()
        
        if node.parent_node >= 0:
            parent_translation, parent_rotation = node_transforms[node.parent_node][:]
            
            abs_rotation    = parent_rotation * rotation
            rel_translation = parent_rotation * translation.to_matrix()
            abs_translation = parent_translation + rel_translation.to_vec3d()
        else:
            abs_translation = translation
            abs_rotation    = rotation
            
        node_transforms.append([abs_translation, abs_rotation])
    
    return node_transforms

    
# Takes a nodes STEPTREE and a set of node transforms [absolute_position, absulute_rotation_matrix]
# and populates the nodes with proper relative positions and rotations.
def SetRelNodetransforms(node_list, node_transforms):
    assert len(node_list) == len(node_transforms), "node_list's length and node_transforms's lengths don't match."

    nodes = copy.deepcopy(node_list)
    
    for i in range(len(nodes)):
        node = nodes[i]
        abs_pos, abs_rot = node_transforms[i][:]
        
        if node.parent_node >= 0:
            parent_abs_pos, parent_abs_rot = node_transforms[node.parent_node][:]
            
            node_rel_pos = (parent_abs_rot.inverse *
                           (abs_pos - parent_abs_pos).to_matrix()
                           ).to_vec3d()
            node.translation[:] = node_rel_pos.unpack()
            
            node_rel_rot = parent_abs_rot.inverse * abs_rot
            node.rotation[:] = node_rel_rot.to_quaternion().unpack()
            
            node.distance_from_parent = node_rel_pos.magnitude
        else:
            node.translation[:] = abs_pos.unpack()
            node.distance_from_parent = 0.0
            
            node.rotation[:] = abs_rot.to_quaternion().unpack()
        
    return nodes
    
    
    
# Takes a list of nodes and sorts it the way Halo likes them. Per level, alphabetical.
def SortNodes(node_list):
    new_nodes = copy.copy(node_list).clear()
    
    levels = [[]]
    ids_to_names = []
    for i in range(len(node_list)):
        node   = node_list[i]
        depth  = 0
        parent = node.parent_node
        
        # loop from our current node to the top so we can get it's depth.
        while node != -1:
            assert depth < 64, "node_list given to SortNodes() has an infinite loop in it, or has way too many nodes."
            parent = node_list[parent].parent_node
            depth += 1
        # afaik I can't really guess the amount of levels we'll have at the end beforehand, so I resorted to this.
        while len(levels) <= depth:
            levels.append([])
            
        levels[depth].append(node)
        ids_to_names.append(node.name)
        
    names_to_new_ids = dict()
    old_ids_to_new_ids = [0] * len(node_list)
    for level in levels:
        level = fstruct.SortSteptreeByNames(level)
        
        for node in level:
            cur_node_id = len(new_nodes)
            old_parent_id = node.parent_node
            if old_parent_id != -1:
                node.parent_node = names_to_new_ids[ids_to_names[old_parent_id]]
            new_nodes.append(node)
            names_to_new_ids.setdefault(node.name, cur_node_id)
            
    
    return new_nodes, translation_list
    
    
    
    