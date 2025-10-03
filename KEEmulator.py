import os
import sys
import shlex
import argparse
import logging
from datetime import datetime

VFS_PATH = None
LOG_PATH = None
SCRIPT_PATH = None

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
    cwd = os.getcwd()
    dir = os.path.expanduser('~')
    if cwd.startswith(dir):
        cwd = '~' + cwd[len(dir):]
    return f"{username}@{hostname}:{cwd}$ "

def parse_cmd(line):
    if not line.strip():
        return None, []
    line = shlex.split(line)
    cmd, args = line[0].lower(), line[1:]
    return cmd, args

def execute_cmd(cmd, args):
    if cmd == 'exit':
        print(f"Exiting KEEmulator.")
        sys.exit(0)
    elif cmd == 'ls':
        result = f"ls {args}"
        print(result)
        return result
    elif cmd == 'cd':
        result = f"cd {args}"
        print(result)
        return result
    else:
        result = f"Command not found: {cmd}"
        print(result)
        return result


def run_script(script_path):
    try:
        with open(script_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                print(get_uhd() + line)
                cmd, args = parse_cmd(line)
                if cmd:
                    result = execute_cmd(cmd, args)
                    if LOG_PATH:
                        logging.info(f'{get_username()},"{line}","{result}"')
                else:
                    if LOG_PATH:
                        logging.info(f'{get_username()},"{line}",""')
    except Exception as e:
        print(f"Error running script: {e}")


if __name__ == '__main__':
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
                    logging.info(f'{get_username()},"{line}","{result}"')
        except KeyboardInterrupt:
            print("\nType 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")

# для тестов
# python KEEmulator.py
# python KEEmulator.py --vfs_path=/home/user/vfs --log_path=emulator.log --script_path=script1.txt
# python KEEmulator.py --vfs_path=/home/user/vfs --log_path=emulator.log --script_path=script2.txt