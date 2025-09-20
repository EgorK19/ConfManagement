import os
import sys
import shlex

def get_uhd():
    try:
        username = os.getlogin()
    except:
        username =  os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
    try:
        if hasattr(os, 'uname'):
            hostname =  os.uname().nodename
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
    try:
        line = shlex.split(line)
        cmd, args = line[0].lower(), line[1:]
        return cmd," ".join(args)
    except Exception as e:
        print(f"Error: {e}")

def execute_cmd(cmd, args):
    if cmd == 'exit':
        print(f"Exiting KEEmulator.")
        sys.exit(0)
    elif cmd == 'ls':
        print(f"ls {args}")
    elif cmd == 'cd':
        print(f"cd {args}")
    else:
        print(f"Command not found: {cmd}")

print("KEEmulator. Type 'exit' to quit.")
while True:
    try:
        line = input(get_uhd())
        cmd, args = parse_cmd(line)
        if cmd:
            execute_cmd(cmd, args)
    except KeyboardInterrupt:
        print("\nType 'exit' to quit")
    except Exception as e:
        print(f"Error: {e}")





