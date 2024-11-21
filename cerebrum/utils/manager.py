import functools

def compare_versions(version1, version2):
    v1_parts = [int(part) for part in version1.split('.')]
    v2_parts = [int(part) for part in version2.split('.')]
    
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1 = v1_parts[i] if i < len(v1_parts) else 0
        v2 = v2_parts[i] if i < len(v2_parts) else 0
        
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    
    return 0

def get_newest_version(version_list):
    print(version_list)
    if version_list == []:
        return None
    return max(version_list, key=functools.cmp_to_key(compare_versions))