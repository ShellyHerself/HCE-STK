from reclaimer.common_descs import *
from supyr_struct.defs.tag_def import TagDef


float_bounds = QStruct('bounds',
    Float('lower'), Float('upper'), ORIENT='h'
    )


general_header = QStruct('header',
    SInt32('count'),
    SInt32('offset')
    )
    
amf_header = Container('amf header',
    SInt32('header'), ## AMF! 0x21464D41
    Float('version'), ## should max be 2.1
    CStrAscii('model name'),
    QStruct("vertices header", INCLUDE=general_header),
    QStruct("markers header", INCLUDE=general_header),
    QStruct("regions header", INCLUDE=general_header),
    QStruct("shaders header", INCLUDE=general_header),
    endian="<"
    )
    
    
vertex_bounds = Struct('vertex bounds',
    QStruct("x_bounds", INCLUDE=float_bounds),
    QStruct("y_bounds", INCLUDE=float_bounds),
    QStruct("z_bounds", INCLUDE=float_bounds),
    QStruct("u_bounds", INCLUDE=float_bounds),
    QStruct("v_bounds", INCLUDE=float_bounds)
    )
    
### node stuff

## Comes right after header

    
node = Container('node',
    CStrAscii('name'),
    SInt16('parent index'),
    SInt16('child index'),
    SInt16('sibling index'),
    QStruct("position", INCLUDE=xyz_float),
    QStruct("orientation", INCLUDE=ijkw_float),
    endian="<"
    )
    

    
amf_def = TagDef('amf',
    amf_header,
    
    Array('vertices',
    SIZE = ".amf_header.vertices_header.count",
    POINTER = ".amf_header.vertices_header.offset",
    SUB_STRUCT = "node"
    ),
    
    ext=".amf", endian="<"
    )
    
def get(): return amf_def