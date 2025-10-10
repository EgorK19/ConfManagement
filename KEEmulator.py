import os
import sys
import shlex
import argparse
import logging
import json
import base64
import datetime
import copy

VFS_PATH = None
LOG_PATH = None
SCRIPT_PATH = None
vfs_root = None
current_vfs_path = []

def setup_args():
    parser = argparse.ArgumentParser(description='KEEmulator')
    parser.add_argument('--vfs_path', type=str, help='Path to VFS physical location')
    parser.add_argument('--log_path', type=str, help='Path to log file')
    parser.add_argument('--script_path', type=str, help='Path to startup script')
    return parser.parse_args()

def setup_logging():
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format='%(asctime)s,%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_username():
    try:
        return os.getlogin()
    except:
        return os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'

def get_uhd():
    try:
        username = get_username()
    except:
        username = 'unknown'
    try:
        if hasattr(os, 'uname'):
            hostname = os.uname().nodename
        else:
            hostname = os.environ.get('COMPUTERNAME', 'unknown-host')
    except:
        hostname = 'unknown-host'

    if vfs_root:
        cwd = '/' + '/'.join(current_vfs_path)
    else:
        cwd = os.getcwd()
        dir = os.path.expanduser('~')
        if cwd.startswith(dir):
            cwd = '~' + cwd[len(dir):]

    return f"{username}@{hostname}:{cwd}$ "

def load_vfs():
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

def parse_cmd(line):
    if not line.strip():
        return None, []
    line = shlex.split(line)
    cmd, args = line[0].lower(), line[1:]
    return cmd, args

def execute_cmd(cmd, args):
    global current_vfs_path

    if cmd == 'exit':
        print(f"Exiting KEEmulator.")
        sys.exit(0)

    elif cmd == 'ls':
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else ''

        if target_path.startswith('/'):
            node = find_vfs_node(target_path)
            full_path = target_path
        else:
            current_dir = '/' + '/'.join(current_vfs_path)
            full_path = current_dir + '/' + target_path if current_dir != '/' else '/' + target_path
            node = find_vfs_node(full_path)

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
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else '/'

        if target_path == '/':
            current_vfs_path = []
            return "Changed to root directory"

        if target_path.startswith('/'):
            new_path = target_path
        else:
            current_dir = '/' + '/'.join(current_vfs_path)
            new_path = current_dir + '/' + target_path if current_dir != '/' else '/' + target_path

        node = find_vfs_node(new_path)

        if not node:
            error = f"cd: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            error = f"cd: {target_path}: Not a directory"
            print(error)
            return error

        path_parts = new_path.strip('/').split('/')
        current_vfs_path = [p for p in path_parts if p]
        return f"Changed to directory {new_path}"

    elif cmd == 'cat':
        if not vfs_root:
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
            current_dir = '/' + '/'.join(current_vfs_path)
            full_path = current_dir + '/' + filename if current_dir != '/' else '/' + filename

        node = find_vfs_node(full_path)

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
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        path = '/' if not current_vfs_path else '/' + '/'.join(current_vfs_path)
        print(path)
        return path

    elif cmd == 'tree':
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else '/' + '/'.join(current_vfs_path)
        if not target_path or target_path == '/':
            node = vfs_root
        else:
            node = find_vfs_node(target_path)

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
        if not vfs_root:
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
            current_dir = '/' + '/'.join(current_vfs_path)
            full_path = current_dir + '/' + filename if current_dir != '/' else '/' + filename

        node = find_vfs_node(full_path)

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
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        username = get_username()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        output = f"{username} pts/0    {current_time}"
        print(output)
        return output

    elif cmd == 'cp':
        if not vfs_root:
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
            current_dir = '/' + '/'.join(current_vfs_path)
            src_full = current_dir + '/' + src if current_dir != '/' else '/' + src
        src_node = find_vfs_node(src_full)
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
            current_dir = '/' + '/'.join(current_vfs_path)
            dest_full = current_dir + '/' + dest if current_dir != '/' else '/' + dest
        dest_node = find_vfs_node(dest_full)

        if dest_node and dest_node['type'] == 'directory':
            src_parent, src_name = get_parent_and_name(src_full)
            dest_parent = dest_node
            dest_name = src_name
            for child in dest_parent.get('children', []):
                if child['name'] == dest_name:
                    error = f"cp: cannot create '{dest}/{dest_name}': File exists"
                    print(error)
                    return error
        else:
            # Treat as new file path
            dest_parent, dest_name = get_parent_and_name(dest_full)
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
        if not vfs_root:
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
            current_dir = '/' + '/'.join(current_vfs_path)
            target_full = current_dir + '/' + target if current_dir != '/' else '/' + target
        target_node = find_vfs_node(target_full)
        if not target_node:
            error = f"rm: cannot remove '{target}': No such file or directory"
            print(error)
            return error
        if target_node.get('type') == 'directory':
            error = f"rm: cannot remove '{target}': Is a directory (use -r for recursive removal)"
            print(error)
            return error

        parent, name = get_parent_and_name(target_full)
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

def run_script(script_path):
    try:
        with open(script_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                print(get_uhd() + line)
                cmd, args = parse_cmd(line)
                if cmd:
                    try:
                        result = execute_cmd(cmd, args)
                        if LOG_PATH:
                            log_event(get_username(), line, result)
                    except Exception as e:
                        error_msg = f"Error in line {line_num}: {e}"
                        print(error_msg)
                        if LOG_PATH:
                            log_event(get_username(), line, f"ERROR: {e}")
                else:
                    if LOG_PATH:
                        log_event(get_username(), line, "")
    except Exception as e:
        print(f"Error running script: {e}")

args = setup_args()

VFS_PATH = args.vfs_path
LOG_PATH = args.log_path
SCRIPT_PATH = args.script_path

print("Launch parameters received:")
print(f"\tVFS_PATH: {VFS_PATH}")
print(f"\tLOG_PATH: {LOG_PATH}")
print(f"\tSCRIPT_PATH: {SCRIPT_PATH}")

if LOG_PATH:
    setup_logging()

if VFS_PATH:
    if load_vfs():
        print("VFS loaded successfully")
    else:
        print("Failed to load VFS")

if SCRIPT_PATH:
    run_script(SCRIPT_PATH)

print("KEEmulator. Type 'exit' to quit.")
while True:
    try:
        prompt = get_uhd()
        line = input(prompt)
        cmd, args = parse_cmd(line)
        if cmd:
            result = execute_cmd(cmd, args)
            if LOG_PATH:
                log_event(get_username(), line, result)
    except KeyboardInterrupt:
        print("\nType 'exit' to quit")
    except Exception as e:
        print(f"Error: {e}")

# для тестов
# Минимальная VFS
# python KEEmulator.py --vfs_path=simpleVFS.json --log_path=emulator.log --script_path=script1.txt

# Расширенная VFS
# python KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=script2.txt

# Полный тест
# python KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=test_script.txt