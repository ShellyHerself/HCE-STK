import copy
from collections import deque

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
    
    
    
    
def CreateNewListUsingIds(old_list, list_of_ids):
    new_list = []
    
    for id in list_of_ids:
        new_list.append(copy.deepcopy(old_list[id]))
        
    return new_list
    
    
# Takes a list, returns a list of all the item names.
# Optional: sorts them alphabetically.
def GetNamesFromSteptree(list, sort_alphabetical = False):
    names = []
    for item in list:
        names.append(item.name)
    if sort_alphabetical:
        names = sorted(names, key=str.lower)
    return names
    
    
    
# Takes a list, returns a copy that is sorted by item name.
def SortSteptreeByNames(list):
    new_list     = copy.copy(list).clear()
    names_sorted = deque(GetNamesFromSteptree(list))
    names_dict   = dict()
    for i in range(len(list)):
        item = list[i]
        names_dict.setdefault(item.name, []).append(i)
        
    n_item = 0
    translation_list = [0] * len(list)
    while len(names_sorted) > 0:
        cur_list = names_sorted.popleft()
        for id in cur_list:
            new_list.append(list[id])
            
            translation_list[id] = n_item
            n_item += 1
            
    return new_list, translation_list
    
    
    
    