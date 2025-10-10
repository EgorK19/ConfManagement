import os
import sys
import shlex
import argparse
import logging
import json
import base64
import datetime

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
        else:
            current_dir = '/' + '/'.join(current_vfs_path)
            full_path = current_dir + '/' + target_path if current_dir != '/' else '/' + target_path
            node = find_vfs_node(full_path)

        if not node:
            error = f"ls: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            error = f"ls: {target_path}: Not a directory"
            print(error)
            return error

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
        current_vfs_path = path_parts
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
            node = find_vfs_node(filename)
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

        path = '/' + '/'.join(current_vfs_path)
        print(path)
        return path

    elif cmd == 'tree':
        if not vfs_root:
            error = "VFS not loaded"
            print(error)
            return error

        target_path = args[0] if args else '/' + '/'.join(current_vfs_path)
        node = find_vfs_node(target_path)

        if not node:
            error = f"tree: {target_path}: No such file or directory"
            print(error)
            return error

        if node.get('type') != 'directory':
            error = f"tree: {target_path}: Not a directory"
            print(error)
            return error

        def print_tree(node, prefix="", is_last=True):
            name = node.get('name', 'unknown')
            if node.get('type') == 'directory':
                result = prefix + ("└── " if is_last else "├── ") + name + "/\n"
                children = node.get('children', [])
                for i, child in enumerate(children):
                    result += print_tree(child, prefix + ("    " if is_last else "│   "), i == len(children) - 1)
            else:
                result = prefix + ("└── " if is_last else "├── ") + name + "\n"
            return result

        tree_output = print_tree(node)
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
            node = find_vfs_node(filename)
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

        lines = content.split('\n')
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
#
# Расширенная VFS
# python KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=script2.txt
#
# Полный тест
# python KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=test_script.txt