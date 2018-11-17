from reclaimer.model.stripify import Stripifier
import math

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
