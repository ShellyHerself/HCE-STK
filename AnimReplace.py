from reclaimer.hek.defs.antr import antr_def
import os
import sys

antr_ext = ".model_animations"


def ReplaceAnimationsWithMatchingNames(dest_tag_path, src_tag_path, safe, copy_indices):
    dest_tag = antr_def.build(filepath=(dest_tag_path + antr_ext))
    src_tag = antr_def.build(filepath=(src_tag_path + antr_ext))
    
    dest_anim_array = dest_tag.data.tagdata.animations
    src_anim_array = src_tag.data.tagdata.animations

    print(dest_anim_array.size)
    print(src_anim_array.size)

    for i in range(0, dest_anim_array.size):
        for j in range(0, src_anim_array.size):
            if (dest_anim_array.STEPTREE[i].name == src_anim_array.STEPTREE[j].name):
                if (copy_indices == True):
                    sys.exit("copy_indices is not implemented.")
                
                if (safe == True):
                    if (dest_anim_array.STEPTREE[i].frame_count != src_anim_array.STEPTREE[j].frame_count):
                        merge_them = input("Found a name match for animation " + dest_anim_array.STEPTREE[i].name
                              + " but the frame counts don't match " + dest_anim_array.STEPTREE[i].frame_count
                              + "!=" + src_anim_array.STEPTREE[j].frame_count + ". Do you still want to copy the data? y/n: ")
                        if merge_them != "y":
                            continue
                            
                if (src_anim_array.STEPTREE[j].frame_count <= 0):
                    continue
                    
                dest_anim_array.STEPTREE[i].frame_count = src_anim_array.STEPTREE[j].frame_count
                dest_anim_array.STEPTREE[i].flags = src_anim_array.STEPTREE[j].flags
                dest_anim_array.STEPTREE[i].unknown_sint16 = src_anim_array.STEPTREE[j].unknown_sint16
                dest_anim_array.STEPTREE[i].unknown_float = src_anim_array.STEPTREE[j].unknown_float
                dest_anim_array.STEPTREE[i].frame_info = src_anim_array.STEPTREE[j].frame_info
                dest_anim_array.STEPTREE[i].trans_flags0 = src_anim_array.STEPTREE[j].trans_flags0
                dest_anim_array.STEPTREE[i].trans_flags1 = src_anim_array.STEPTREE[j].trans_flags1
                dest_anim_array.STEPTREE[i].rot_flags0 = src_anim_array.STEPTREE[j].rot_flags0
                dest_anim_array.STEPTREE[i].rot_flags1 = src_anim_array.STEPTREE[j].rot_flags1
                dest_anim_array.STEPTREE[i].scale_flags0 = src_anim_array.STEPTREE[j].scale_flags0
                dest_anim_array.STEPTREE[i].scale_flags1 = src_anim_array.STEPTREE[j].scale_flags1
                dest_anim_array.STEPTREE[i].offset_to_compressed_data = src_anim_array.STEPTREE[j].offset_to_compressed_data
                dest_anim_array.STEPTREE[i].default_data = src_anim_array.STEPTREE[j].default_data
                dest_anim_array.STEPTREE[i].frame_data = src_anim_array.STEPTREE[j].frame_data

                print("Copied data to #" + str(i) + " " + dest_anim_array.STEPTREE[j].name + " from #" + str(j) + " " + src_anim_array.STEPTREE[j].name)
        
    dest_tag.serialize(temp=False, backup=True)
    src_tag.serialize(temp=True, backup=False)
    os.remove(src_tag_path + antr_ext + ".temp")
    
#end

#Only run this if the script is ran directly
if __name__ == '__main__':
    from argparse import ArgumentParser

    #Initialise startup arguments
    parser = ArgumentParser(description='Animation replacer for halo editing kit tags. Meant for repairing animation graphs after tool has broken them during compression.')
    parser.add_argument('-s', '--safe', dest='safe', action='store_const',
                        const=True, default=False,
                        help='Prompts you if the animations in the tags you are trying to merge have inconsistent amounts of frames.')
    parser.add_argument('-c', '--copy-frame-indices-and-sounds', dest='copy', action='store_const',
                        const=True, default=False,
                        help='Copies the keyframe and sound info from the compressed tag. (Disabled by default because usually only the destination tag has proper frame indices.')
    parser.add_argument('destination_tag', metavar='destination_tag', type=str,
                        help='The tag you want to replace the animations of.')
    parser.add_argument('source_tag', metavar='source_tag', type=str,
                        help='The tag you want to read the animations from.')
    args = parser.parse_args()

    #Remove any occurences of the file extension in the paths
    destination_tag = args.destination_tag.replace(antr_ext, "")
    source_tag = args.source_tag.replace(antr_ext, "")
    
    #Check if the file exists in both a path relative to the location the script is being executed from
    #and if it can't find it there, look for it as an absolute path
    if (os.path.isfile(os.path.join('./', destination_tag + antr_ext))):
        destination_tag = os.path.join('./', destination_tag)
    elif (os.path.isfile(destination_tag + antr_ext)):
        destination_tag = destination_tag
    else:
        sys.exit("The file " + destination_tag + antr_ext + " does not exist.")

    if (os.path.isfile(os.path.join('./', source_tag + antr_ext))):
        source_tag = os.path.join('./', source_tag)
    elif (os.path.isfile(source_tag + antr_ext)):
        source_tag = source_tag
    else:
        sys.exit("The file " + source_tag + antr_ext + " does not exist.")

    ReplaceAnimationsWithMatchingNames(destination_tag, source_tag, args.safe, args.copy)

    print("Finished.")
#end
