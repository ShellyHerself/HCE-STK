import os
import sys

#Check if the file exists in both a path relative to the location the script is being executed from
#and if it can't find it there, look for it as an absolute path
def GetAbsFilepath(filepath, extension):

    if (os.path.isfile(os.path.join('./',  filepath + extension))):
        filepath = os.path.join('./', filepath)
    elif (os.path.isfile(filepath + extension)):
        filepath = filepath
    else:
        sys.exit("The file " + filepath + extension + " does not exist.\n")

    return filepath
