from map_spoof_checksum import MapGetChecksum

if __name__ == '__main__':
    from argparse import ArgumentParser
    
    #Initialise startup arguments
    parser = ArgumentParser(description="Gets and prints the hex checksum for a given Halo CE map.")
    parser.add_argument('map_filepath', metavar='map', type=str,
                        help="The map we get the checksum from.")
    args = parser.parse_args()
    
    from shared.SharedFunctions import GetAbsFilepath
    
    map_filepath = GetAbsFilepath(args.map_filepath, ".map") + ".map"
    header_checksum, calculated_checksum = MapGetChecksum(map_filepath)
    print("Header checksum for", map_filepath, "is", "%0.8X" % header_checksum)
    print("Calculated checksum checksum for", map_filepath, "is", "%0.8X" % calculated_checksum)

