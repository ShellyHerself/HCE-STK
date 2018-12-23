from reclaimer.model.stripify import Stripifier
from reclaimer.hek.defs.objs.matrices import quaternion_to_matrix as QuaternionToMatrix
from reclaimer.hek.defs.objs.matrices import matrix_to_quaternion as MatrixToQuaternion
from reclaimer.hek.defs.objs.matrices import multiply_quaternions as MultiplyQuaternions
from reclaimer.hek.defs.objs.matrices import Matrix
import copy
import math

def InvertQuat(quat):
    return -quat[0], -quat[1], -quat[2], quat[3]
def InvertQuat2(quat):
    return -quat[0], -quat[1], -quat[2], -quat[3]

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
        translation = node.translation
        rotation = node.rotation
        x, y, z = translation[:]
        this_translation = copy.deepcopy(translation)
        this_rotation = QuaternionToMatrix(*rotation)
        
        if node.parent_node >= 0:
            parent = node_transforms[node.parent_node]
            translation = Matrix((z, y, z))
            
            parent_rotation = parent[1]
            this_rotation = parent_rotation * this_rotation
            
            translation = parent_rotation * translation
            x = translation[0][0] + parent[0][0]
            y = translation[1][0] + parent[0][1]
            z = translation[2][0] + parent[0][2]
            
        this_translation[:] = [x, y, z]
        node_transforms.append([this_translation, this_rotation])

    return node_transforms

# Takes a nodes STEPTREE and a set of node transforms [absolute_position, absulute_rotation_matrix] and populates the nodes with proper relative positions and rotations.
def SetRelNodetransforms(node_list, node_transforms):
    assert len(node_list) == len(node_transforms), "node_list's length and node_transforms's lengths don't match.\n Can't properly execute function."
    
    nodes = copy.deepcopy(node_list)
    
    for i in range(len(nodes)):
        node = nodes[i]
        abs_pos, abs_rot = node_transforms[i][:]
        
        if node.parent_node != -1:
            parent_abs_pos, parent_abs_rot = node_transforms[node.parent_node][:]
        
            node_rel_pos = Matrix((abs_pos[0] - parent_abs_pos[0],
                                   abs_pos[1] - parent_abs_pos[1],
                                   abs_pos[2] - parent_abs_pos[2]))
            node_rel_pos = parent_abs_rot.inverse * node_rel_pos
            node.translation.x = node_rel_pos[0][0]
            node.translation.y = node_rel_pos[1][0]
            node.translation.z = node_rel_pos[2][0]
            
            node_rel_rot = MatrixToQuaternion((parent_abs_rot.inverse * abs_rot))
            node.rotation[:] = node_rel_rot[:]
            
            node.distance_from_parent = math.sqrt(node.translation.x**2 + node.translation.y**2 + node.translation.z**2)
        else:
            node.translation[:] = abs_pos[:]
            node.distance_from_parent = 0.0
            
            node_rel_rot = MatrixToQuaternion(abs_rot)
            node.rotation[:] = node_rel_rot[:]
        
        
    return nodes
        
'''
#My math test
bone1 = [[0.0146143, 3e-008, 0.440025], [0.499999, 0.5, 0.499999, 0.500001]]
bone2 = [[-6e-008, 5e-008, 0.0398455], [-0.276799, -0.960126, -0.010875, -0.037722]]
#print("bone1 before:\n", bone1)
print("bone2 before:\n", bone2)
print("")
bone1_pos_mat = Matrix((bone1[0][0], bone1[0][1], bone1[0][2]))
bone2_pos_mat = Matrix((bone2[0][0], bone2[0][1], bone2[0][2]))
bone1_rot_mat = QuaternionToMatrix(*InvertQuat([bone1[1][0], bone1[1][1], bone1[1][2], bone1[1][3]]))
bone2_rot_mat = QuaternionToMatrix(*InvertQuat([bone2[1][0], bone2[1][1], bone2[1][2], bone2[1][3]]))


bone2_abs_rot_mat = bone1_rot_mat * bone2_rot_mat
bone2_unrot_pos_mat = bone1_rot_mat * bone2_pos_mat
bone2_abs_pos = [bone1[0][0] + bone2_unrot_pos_mat[0][0],
                 bone1[0][1] + bone2_unrot_pos_mat[1][0],
                 bone1[0][2] + bone2_unrot_pos_mat[2][0]]
bone2_abs_rot = MatrixToQuaternion(bone2_abs_rot_mat)
bone2_between = [bone2_abs_pos, list(bone2_abs_rot)]
print("bone2 between:\n", bone2_between)
print("")

bone2_rel_pos = [bone2_between[0][0] - bone1[0][0],
                 bone2_between[0][1] - bone1[0][1],
                 bone2_between[0][2] - bone1[0][2]]
bone2_rel_pos = bone1_rot_mat.inverse * Matrix(bone2_rel_pos)
bone2_after = [bone2_rel_pos, list(InvertQuat(MatrixToQuaternion((bone1_rot_mat.inverse * bone2_abs_rot_mat))))]

print("bone2 after:\n", bone2_after)
print("")
'''