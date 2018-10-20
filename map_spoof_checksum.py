import os
import gc
import sys
from os.path import abspath, dirname, exists, isfile, join

from reclaimer.meta.halo_map import get_map_header, get_index_magic
from refinery import crc_functions

# MapSpoofChecksum() is written by MosesOfEgypt.
def MapSpoofChecksum(in_filepath, out_filepath, crc):

    if not out_filepath:
        out_filepath = in_filepath

    in_filepath = abspath(in_filepath)
    out_filepath = abspath(out_filepath)
    crc = crc & 0xFFffFFff
    if not isfile(in_filepath):
        print("Specified input map does not exist.")
        return

    try:
        os.makedirs(join(dirname(out_filepath), ""), True)
    except FileExistsError:
        pass

    # use r+ mode rather than w if the file exists
    # since it might be hidden. apparently on windows
    # the w mode will fail to open hidden files.
    if in_filepath.lower() == out_filepath.lower():
        in_file = out_file = open(in_filepath, 'r+b')
    else:
        in_file = open(in_filepath, 'rb')
        if isfile(out_filepath):
            out_file = open(out_filepath, 'r+b')
            out_file.truncate(0)
        else:
            out_file = open(out_filepath, 'w+b')

    map_header = get_map_header(in_file.read(2048))
    if map_header is None:
        print("Input file does not appear to be a halo map.")
        return
    elif map_header.version.enum_name != "halo1ce":
        print("Input file does not appear to be a halo custom edition map.")
        return

    index_magic = get_index_magic(map_header)
    in_file.seek(0)
    if in_file is not out_file:
        # copy the map to the location
        chunk = True
        while chunk:
            chunk = in_file.read(4*1024**2)  # work with 4Mb chunks
            out_file.write(chunk)
            gc.collect()

        in_file.close()
        out_file.flush()

    map_header.crc32 = crc
    crc_functions.E.__defaults__[0][:] = [0, 0x800000000 - crc, crc]
    out_file.seek(0)
    out_file.write(map_header.serialize(calc_pointers=False))
    out_file.flush()
    if hasattr(out_file, "fileno"):
        os.fsync(out_file.fileno())

    # write the map header so the calculate_ce_checksum can read it
    crc_functions.U(
        [crc_functions.calculate_ce_checksum(out_file, index_magic)^0xFFffFFff,
         out_file, map_header.tag_index_header_offset + 8])

    out_file.flush()
    if hasattr(out_file, "fileno"):
        os.fsync(out_file.fileno())

    out_file.close()


def MapGetChecksum(map_filepath):
    map = open(map_filepath, 'r+b')

    map_header = get_map_header(map.read(2048))
    if map_header is None:
        print("Input file does not appear to be a halo map.")
        return
    elif map_header.version.enum_name != "halo1ce":
        print("Input file does not appear to be a halo custom edition map.")
        return
    header_checksum = map_header.crc32
    calculated_checksum = crc_functions.calculate_ce_checksum(map, get_index_magic(map_header))
    map.close()
    return header_checksum, calculated_checksum


#Only run this if the script is ran directly
if __name__ == '__main__':
    from argparse import ArgumentParser
    
    #Initialise startup arguments
    parser = ArgumentParser(description='Halo CE Mapfile checksum spoofer. Used to make new versions of maps compatible with an old version so they can play online together. If no checksum source is specified we will take the checksum number from the input map header and make sure the map gives this same checksum when calculated by the game.')
    parser.add_argument('-i', '--input', dest='map_in', type=str,
                        help='Sets the map we spoof. If this arg is not used we spoof the map from the output arg.')
    parser.add_argument('-c', '--checksum', dest='checksum', type=str,
                        help='Absolute checksum you want to give the map. This is a hex number.')
    parser.add_argument('-m', '--copy-checksum-from', dest='checksum_map', type=str,
                        help='Makes the program copy the checksum from the map given in this argument.')
    parser.add_argument('-k', '--calculate-checksum', dest='calc_checksum', action='store_true',
                        help='Calculates the checksum instead of taking it from the header. AFFECTS: --copy-checksum-from')
    parser.add_argument('output', metavar='map_out', type=str,
                        help="The map file we'll be saving our changes to.")
    args = parser.parse_args()
    
    from shared.SharedFunctions import GetAbsFilepath
    
    map_out = args.output + ".map"
    
    if args.map_in:
        map_in = GetAbsFilepath(args.map_in, ".map") + ".map"
    else:
        map_in = map_out
        
    if args.checksum:
        checksum = args.checksum
        try:
            crc = int(checksum.replace(" ", ""), 16)
        except ValueError:
            print("Invalid crc checksum. Must be an 8 character hex string")
        
    if args.checksum_map:
        checksum_map = GetAbsFilepath(args.checksum_map, ".map") + ".map"
        
    if args.checksum:
        print("Spoofing map using provided checksum number.")
        sys.stdout.flush()
        MapSpoofChecksum(map_in, map_out, crc)
    elif args.checksum_map:
        print("Spoofing map by using checksum from provided checksum map.")
        sys.stdout.flush()
        header_checksum, calculated_checksum = MapGetChecksum(checksum_map)
        if not calc_checksum:
            MapSpoofChecksum(map_in, map_out, header_checksum)
        else:
            MapSpoofChecksum(map_in, map_out, calculated_checksum)
    else:
        print("Spoofing map using it's own checksum number. (Aligning the data to match the checksum.)")
        sys.stdout.flush()
        MapSpoofChecksum(map_in, map_out, MapGetChecksum(map_in))
    
    print("finished\n")
