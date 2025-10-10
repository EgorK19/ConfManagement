import json

vfs_root = None
current_vfs_path = []

def load_vfs(VFS_PATH):
    global vfs_root, current_vfs_path
    if not VFS_PATH:
        return False
    try:
        with open(VFS_PATH, 'r') as f:
            vfs_root = json.load(f)
        current_vfs_path = []
        return True
    except Exception as e:
        print(f"Error loading VFS: {e}")
        return False

def find_vfs_node(path):
    if not vfs_root:
        return None

    if not path or path == '/':
        return vfs_root

    path_parts = path.strip('/').split('/')
    current_node = vfs_root

    for part in path_parts:
        if part == '':
            continue

        if current_node.get('type') != 'directory':
            return None

        found = False
        for child in current_node.get('children', []):
            if child.get('name') == part:
                current_node = child
                found = True
                break

        if not found:
            return None

    return current_node

def get_current_vfs_node():
    current_path = '/' + '/'.join(current_vfs_path)
    return find_vfs_node(current_path)

def get_parent_and_name(path):
    if not path or path == '/':
        return None, ''

    path_parts = path.strip('/').split('/')
    parent_path = '/' + '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
    name = path_parts[-1]
    parent = find_vfs_node(parent_path)
    return parent, name
