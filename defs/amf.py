from reclaimer.common_descs import *
from supyr_struct.defs.tag_def import TagDef
import math


def get_vert_node_count(rawdata=None, **kwargs):
    indices = rawdata.peek(4)
    if   indices[1] == 255: return 1
    elif indices[2] == 255: return 2
    elif indices[3] == 255: return 3
    else: return 4

def get_vert_node_weight_count(parent=None, **kwargs):
    if parent.node_indices[-1] != 255:
        return 4
    return len(parent.node_indices) - 1

def is_vert_count_over_65535(parent=None, **kwargs):
    if parent is None:
        raise KeyError('Cannot determine case without parent.')
    return parent.parent.vertices_header.field_count > 65535

def get_has_extra_block(parent=None, **kwargs):
    if parent is None:
        raise KeyError('Cannot determine case without parent.')
    return math.isnan(parent.mult)

def amf_newer_than_11(parent=None, **kwargs):
    if parent.get_root().data.version > 1.1:
        return True
    return False
    
float_bounds = QStruct('bounds',
    Float('lower'), Float('upper'), ORIENT='h'
    )

general_header = QStruct('header',
    SInt32('field count', VISIBLE=False),
    SInt32('array address', VISIBLE=False)
    )
    
vertex_bounds = Struct('bounds',
    QStruct('x', INCLUDE=float_bounds),
    QStruct('y', INCLUDE=float_bounds),
    QStruct('z', INCLUDE=float_bounds),
    QStruct('u', INCLUDE=float_bounds),
    QStruct('v', INCLUDE=float_bounds)
    )
    
node = Container('node',
    CStrUtf8('name'),
    SInt16('parent index'),
    SInt16('child index'),
    SInt16('sibling index'),
    QStruct('position', INCLUDE=xyz_float),
    QStruct('orientation', INCLUDE=ijkw_float)
)
    
marker_instance = Struct('instance',
    SInt8('region index'),
    SInt8('permutation index'),
    SInt16('node index'),
    QStruct('position', INCLUDE=xyz_float),
    QStruct('orientation', INCLUDE=ijkw_float)
)
    
marker = Container('marker',
    CStrUtf8('name'),
    Struct('marker instances',
        INCLUDE=general_header,
        STEPTREE=Array('instances',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = marker_instance
        )
    )
)

vertex_compressed = Struct('vertex',
    QStruct('position', SInt16('x', UNIT_SCALE=1/32767), SInt16('y', UNIT_SCALE=1/32767), SInt16('z', UNIT_SCALE=1/32767)),
    BitStruct('normal', INCLUDE=compressed_normal_32, SIZE=4),
    SInt16('u', UNIT_SCALE=1/32767),
    SInt16('v', UNIT_SCALE=1/32767)
)

vertex_uncompressed = Struct('vertex',
    QStruct('position', INCLUDE=xyz_float),
    QStruct('normal', INCLUDE=ijk_float),
    Float('u'),
    Float('v')
)

vert_indices_1 = QStruct('vert_indices',
    UInt8('node index 1'),
    UInt8('node index 2', DEFAULT=255, VISIBLE=False)
)
vert_indices_2 = QStruct('vert_indices',
    UInt8('node index 1'),
    UInt8('node index 2'),
    UInt8('node index 3', DEFAULT=255, VISIBLE=False)
)
vert_indices_3 = QStruct('vert_indices',
    UInt8('node index 1'),
    UInt8('node index 2'),
    UInt8('node index 3'),
    UInt8('node index 4', DEFAULT=255, VISIBLE=False)
)
vert_indices_4 = QStruct('vert_indices',
    UInt8('node index 1'),
    UInt8('node index 2'),
    UInt8('node index 3'),
    UInt8('node index 4'),
)

vert_weights_1 = QStruct('vert_weights',
    Float('node weight 1'),
)
vert_weights_2 = QStruct('vert_weights',
    Float('node weight 1'),
    Float('node weight 2'),
)
vert_weights_3 = QStruct('vert_weights',
    Float('node weight 1'),
    Float('node weight 2'),
    Float('node weight 3'),
)
vert_weights_4 = QStruct('vert_weights',
    Float('node weight 1'),
    Float('node weight 2'),
    Float('node weight 3'),
    Float('node weight 4'),
)

vertex_format_0 = Container('vertex',
    Switch('data',
        DEFAULT=vertex_uncompressed,
        CASE='.....format_info.compression_format',
        CASES={1: vertex_compressed,
               2: vertex_compressed,
               3: vertex_compressed}
    )
)

vertex_format_1 = Container('vertex',
    Switch('data',
        DEFAULT=vertex_uncompressed,
        CASE='.....format_info.compression_format',
        CASES={1: vertex_compressed,
               2: vertex_compressed,
               3: vertex_compressed}
    ),
    Switch('node indices',
        CASE=get_vert_node_count,
        CASES={1: vert_indices_1,
               2: vert_indices_2,
               3: vert_indices_3,
               4: vert_indices_4}
    ),

    Switch('weights',
        CASE=get_vert_node_weight_count,
        CASES={1: vert_weights_1,
               2: vert_weights_2,
               3: vert_weights_3,
               4: vert_weights_4}
    )
)

vertex_format_2 = Container('vertex',
    Switch('data',
        DEFAULT=vertex_uncompressed,
        CASE='.....format_info.compression_format',
        CASES={1: vertex_compressed,
               2: vertex_compressed,
               3: vertex_compressed}
    ),
    Switch('node indices',
        CASE=get_vert_node_count,
        CASES={1: vert_indices_1,
               2: vert_indices_2,
               3: vert_indices_3,
               4: vert_indices_4}
    )
)

vertex_format_0_array = Array('vertices array',
    SIZE = '..field_count',
    SUB_STRUCT=vertex_format_0
)
vertex_format_1_array = Array('vertices array',
    SIZE = '..field_count',
    SUB_STRUCT=vertex_format_1
)
vertex_format_2_array = Array('vertices array',
    SIZE = '..field_count',
    SUB_STRUCT=vertex_format_2
)

vertices = Container('vertices',
    Switch('bounds',
        CASE='...format_info.compression_format',
        CASES={1: vertex_bounds}
    ),
    Switch('vertices',
        CASE='...format_info.vertex_format',
        CASES={0: vertex_format_0_array,
               1: vertex_format_1_array,
               2: vertex_format_2_array}
    ),
    POINTER='.array_address'
)
    
two_byte_face = Container('face',
    UInt16('v1'), UInt16('v2'), UInt16('v3')
)

four_byte_face = Container('face',
    UInt32('v1'), UInt32('v2'), UInt32('v3')
)

two_byte_face_array = Array('faces',
    SIZE = '.field_count',
    SUB_STRUCT=two_byte_face
)
four_byte_face_array = Array('faces',
    SIZE = '.field_count',
    SUB_STRUCT=four_byte_face
)
    
faces = Switch('faces',
        CASE=is_vert_count_over_65535,
        CASES={True: four_byte_face_array,
               False: two_byte_face_array},
        POINTER='.array_address'
)

section = Struct('section',
    SInt16('shader index'),
    SInt32('starting face'),
    SInt32('face count')
)

sections = Array('sections',
    SIZE = '.field_count',
    SUB_STRUCT=section,
    POINTER='.array_address'
)

transformation_matrix = Struct('transformation matrix',
    QStruct('row1', INCLUDE=xyz_float),
    QStruct('row2', INCLUDE=xyz_float),
    QStruct('row3', INCLUDE=xyz_float),
    QStruct('row4', INCLUDE=xyz_float)
)

permutation = Container('permutation',
    CStrUtf8('name'),
    BitStruct('format_info',
        S1BitInt('vertex format', SIZE=4),
        S1BitInt('compression format', SIZE=4)
    ),
    SInt8('node index'),
    QStruct('vertices header',
        INCLUDE=general_header,
        STEPTREE=vertices
    ),
    Struct('faces header',
        INCLUDE=general_header,
        STEPTREE=faces
    ),
    Struct('sections header',
        INCLUDE=general_header,
        STEPTREE=sections
    ),
    Float('mult'),
    Switch('transformation matrix',
        CASE=get_has_extra_block,
        CASES={False: transformation_matrix}
    )
)

region = Container('region',
    CStrUtf8('name'),
    Struct('permutations header',
        INCLUDE=general_header,
        STEPTREE=Array('permutations',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = permutation
        )
    )
)
    
def is_path_valid(parent=None, **kwargs):
    if parent.filepath != 'null':
        return True
    return False
    
bitmap = Container('bitmap',
    CStrUtf8('filepath'),
    Switch('tiling',
        CASE=is_path_valid,
        CASES={True: uv_float}
    )
)

bitmap2 = Container('bitmap',
    CStrUtf8('filepath'),
    uv_float
)

normal_shader_colors = Array('colors',
    SUB_STRUCT=argb_byte,
    SIZE=4
)

normal_shader = Container('normal shader',
    Array('bitmaps',
        SUB_STRUCT=bitmap,
        SIZE=8
    ),
    Switch('colors',
        CASE=amf_newer_than_11,
        CASES={True:normal_shader_colors}
    ),
    SInt8('is transparent'),
    SInt8('cc only')
)

terrain_shader = Container('terrain shader',
    Container('blend', INCLUDE=bitmap),
    SInt8('basemap count'),
    SInt8('bumpmap count'),
    SInt8('detailmap count'),
    Array('basemaps', SIZE='.basemap_count', SUB_STRUCT=bitmap2),
    Array('bumpmaps', SIZE='.bumpmap_count', SUB_STRUCT=bitmap2),
    Array('detailmaps', SIZE='.detailmap_count', SUB_STRUCT=bitmap2)
)


def shader_type_sig_size(rawdata=None, **kwargs):
    if rawdata is None or rawdata.peek(1) != b'*':
        return 0
    return 1

def is_terrain_shader(parent=None, **kwargs):
    if parent.type_sig == '*':
        return True
    return False

shader = Container('shader',
    StrRawLatin1('type sig', SIZE=shader_type_sig_size),
    CStrUtf8('name'),
    Switch('type',
        CASE=is_terrain_shader,
        CASES={False:normal_shader,
               True:terrain_shader}
    )
)
    
    
amf_def = TagDef('amf',
    StrRawUtf8('header', SIZE = 4, DEFAULT='AMF!' ),
    Float('version', DEFAULT=2.1), ## should max be 2.1
    CStrUtf8('model name'),
    Struct('nodes header',
        INCLUDE=general_header,
        STEPTREE=Array('nodes',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = node
        )
    ),
    Struct('markers header',
        INCLUDE=general_header,
        STEPTREE=Array('markers',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = marker
        )
    ),
    Struct('regions header',
        INCLUDE=general_header,
        STEPTREE=Array('regions',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = region
        )
    ),
    Struct('shaders header',
        INCLUDE=general_header,
        STEPTREE=Array('shaders',
        SIZE = '.field_count',
        POINTER = '.array_address',
        SUB_STRUCT = shader
        )
    ),
    ext='.amf', endian='<'
)
    
def get(): return amf_def
