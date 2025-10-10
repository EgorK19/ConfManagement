import sys
import base64
import datetime
import copy
import logging
import vfs
from utils import get_username

def parse_cmd(line):
    import shlex
    if not line.strip():
        return None, []
    line = shlex.split(line)
    cmd, args = line[0].lower(), line[1:]
    return cmd, args

def execute_cmd(cmd, args):
    # использование vfs.current_vfs_path внутри модуля vfs
    if cmd == 'exit':
        print(f"Exiting KEEmulator.")
        sys.exit(0)

    elif cmd == 'ls':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else ''

        if target_path.startswith('/'):
            node = vfs.find_vfs_node(target_path)
            full_path = target_path
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            full_path = current_dir + '/' + target_path if current_dir != '/' else '/' + target_path
            node = vfs.find_vfs_node(full_path)

        if not node:
            error = f"ls: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            print(node['name'])  # If it's a file, just print its name
            return node['name']

        result = []
        for child in node.get('children', []):
            if child.get('type') == 'directory':
                result.append(f"{child['name']}/")
            else:
                result.append(child['name'])

        output = '  '.join(result)
        print(output)
        return output

    elif cmd == 'cd':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else '/'

        if target_path == '/':
            vfs.current_vfs_path = []
            return "Changed to root directory"

        if target_path.startswith('/'):
            new_path = target_path
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            new_path = current_dir + '/' + target_path if current_dir != '/' else '/' + target_path

        node = vfs.find_vfs_node(new_path)

        if not node:
            error = f"cd: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            error = f"cd: {target_path}: Not a directory"
            print(error)
            return error

        path_parts = new_path.strip('/').split('/')
        vfs.current_vfs_path = [p for p in path_parts if p]
        return f"Changed to directory {new_path}"

    elif cmd == 'cat':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        if not args:
            error = "cat: missing file operand"
            print(error)
            return error

        filename = args[0]

        if filename.startswith('/'):
            full_path = filename
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            full_path = current_dir + '/' + filename if current_dir != '/' else '/' + filename

        node = vfs.find_vfs_node(full_path)

        if not node:
            error = f"cat: {filename}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'file':
            error = f"cat: {filename}: Is a directory"
            print(error)
            return error

        content = node.get('content', '')
        encoding = node.get('encoding', 'text')

        if encoding == 'base64':
            try:
                content = base64.b64decode(content).decode('utf-8')
            except:
                error = f"cat: {filename}: Error decoding base64 content"
                print(error)
                return error

        print(content)
        return f"Displayed content of {filename}"

    elif cmd == 'pwd':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        path = '/' if not vfs.current_vfs_path else '/' + '/'.join(vfs.current_vfs_path)
        print(path)
        return path

    elif cmd == 'tree':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else '/' + '/'.join(vfs.current_vfs_path)
        if not target_path or target_path == '/':
            node = vfs.vfs_root
        else:
            node = vfs.find_vfs_node(target_path)

        if not node:
            error = f"tree: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            error = f"tree: {target_path}: Not a directory"
            print(error)
            return error

        def print_tree(current, prefix="", is_last=True, is_root=True):
            if is_root:
                name = "root/" if target_path == '/' else current.get('name', '') + '/'
            else:
                name = current.get('name', '')
            line = prefix + ("└── " if is_last else "├── ") + name
            if current.get('type') == 'directory':
                line += "/" if not is_root else ""
            result = line + "\n"
            if current.get('type') == 'directory':
                children = current.get('children', [])
                for i, child in enumerate(sorted(children, key=lambda x: x['name'])):
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    result += print_tree(child, new_prefix, i == len(children) - 1, False)
            return result

        tree_output = print_tree(node, is_root=True)
        print(tree_output)
        return tree_output

    elif cmd == 'uniq':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        if not args:
            error = "uniq: missing operand"
            print(error)
            return error

        filename = args[0]

        if filename.startswith('/'):
            full_path = filename
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            full_path = current_dir + '/' + filename if current_dir != '/' else '/' + filename

        node = vfs.find_vfs_node(full_path)

        if not node:
            error = f"uniq: {filename}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'file':
            error = f"uniq: {filename}: Is a directory"
            print(error)
            return error

        content = node.get('content', '')
        encoding = node.get('encoding', 'text')

        if encoding == 'base64':
            try:
                content = base64.b64decode(content).decode('utf-8')
            except:
                error = f"uniq: {filename}: Error decoding base64 content"
                print(error)
                return error

        lines = content.splitlines()
        unique_lines = []
        for line in lines:
            if not unique_lines or line != unique_lines[-1]:
                unique_lines.append(line)

        output = '\n'.join(unique_lines)
        print(output)
        return f"Displayed unique lines from {filename}"

    elif cmd == 'who':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        username = get_username()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        output = f"{username} pts/0    {current_time}"
        print(output)
        return output

    elif cmd == 'cp':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        if len(args) != 2:
            error = "cp: missing source or destination operand"
            print(error)
            return error

        src = args[0]
        dest = args[1]

        if src.startswith('/'):
            src_full = src
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            src_full = current_dir + '/' + src if current_dir != '/' else '/' + src
        src_node = vfs.find_vfs_node(src_full)
        if not src_node:
            error = f"cp: cannot stat '{src}': No such file or directory"
            print(error)
            return error
        if src_node.get('type') == 'directory':
            error = f"cp: omitting directory '{src}' (use -r for recursive copy)"
            print(error)
            return error

        if dest.startswith('/'):
            dest_full = dest
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            dest_full = current_dir + '/' + dest if current_dir != '/' else '/' + dest
        dest_node = vfs.find_vfs_node(dest_full)

        if dest_node and dest_node['type'] == 'directory':
            src_parent, src_name = vfs.get_parent_and_name(src_full)
            dest_parent = dest_node
            dest_name = src_name
            for child in dest_parent.get('children', []):
                if child['name'] == dest_name:
                    error = f"cp: cannot create '{dest}/{dest_name}': File exists"
                    print(error)
                    return error
        else:
            # Treat as new file path
            dest_parent, dest_name = vfs.get_parent_and_name(dest_full)
            if not dest_parent:
                error = f"cp: cannot create '{dest}': Invalid path"
                print(error)
                return error
            if dest_node:
                error = f"cp: cannot overwrite '{dest}': File exists"
                print(error)
                return error

        copied_node = copy.deepcopy(src_node)
        copied_node['name'] = dest_name
        dest_parent['children'].append(copied_node)
        output = f"Copied '{src}' to '{dest}'"
        print(output)
        return output

    elif cmd == 'rm':
        if not vfs.vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        if not args:
            error = "rm: missing operand"
            print(error)
            return error

        target = args[0]

        if target.startswith('/'):
            target_full = target
        else:
            current_dir = '/' + '/'.join(vfs.current_vfs_path)
            target_full = current_dir + '/' + target if current_dir != '/' else '/' + target
        target_node = vfs.find_vfs_node(target_full)
        if not target_node:
            error = f"rm: cannot remove '{target}': No such file or directory"
            print(error)
            return error
        if target_node.get('type') == 'directory':
            error = f"rm: cannot remove '{target}': Is a directory (use -r for recursive removal)"
            print(error)
            return error

        parent, name = vfs.get_parent_and_name(target_full)
        if not parent:
            error = "rm: cannot remove root"
            print(error)
            return error
        parent['children'] = [child for child in parent['children'] if child['name'] != name]
        output = f"Removed '{target}'"
        print(output)
        return output

    else:
        result = f"Command not found: {cmd}"
        print(result)
        return result

def log_event(username, command, result):
    command_escaped = command.replace('"', '""')
    result_escaped = result.replace('"', '""') if result else ""
    logging.info(f'{username},"{command_escaped}","{result_escaped}"')
