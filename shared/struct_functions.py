import copy

# Takes a list where each entry has the attribute name and returns the list but with lower case names.
def ConvertListEntryNamesToLowercase(list):
    for entry in list:
        entry.name = entry.name.lower()
    
    return list

# Takes a list where each entry has the attribute name and returns a copy that is sorted by those copies.
def SortListByEntryNames(list):
    new_list = []
    old_list = copy.copy(list)
    names = []
    
    for entry in old_list:
        names.append(entry.name)
        
    names = sorted(names, key=str.lower)
    
    for name in names:
        for i in range(len(old_list)):
            if old_list[i].name == name:
                new_list.append(old_list.pop(i))
                break
    
    return new_list
    
def ConvertListEntryNamesFromNewStdToCE(list, regions=False):
    conversion_list = [
        ["default" , "__base"]
    ]
    if regions:
        conversion_list[0] == ["default", "__unamed"]
    
    for entry in list:
        for conv in conversion_list:
            if entry.name == conv[0]:
                entry.name = conv[1]
                
    return list
    
    
def CreateCutDownListUsingLeftoverIds(old_list, list_of_ids):
    new_list = []
    
    for id in list_of_ids:
        new_list.append(copy.deepcopy(old_list[id]))
        
    return new_list