import os
import sys
import shlex

def get_uhd():
    username = os.getlogin()
    hostname = os.uname().nodename if hasattr(os, 'uname') else os.environ['COMPUTERNAME']
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
    return cmd," ".join(args)

def execute_cmd(cmd, args,t):
    if cmd == 'exit':
        print(f"{t}Exiting KEEmulator.")
        sys.exit(0)
    elif cmd == 'ls':
        print(f"ls {args}")
    elif cmd == 'cd':
        print(f"cd {args}")
    else:
        print(f"{t}command not found: {cmd}")

print("KEEmulator. Type 'exit' to quit.")
while True:
    t = get_uhd()
    try:
        line = input(t)
        cmd, args = parse_cmd(line)
        if cmd:
            execute_cmd(cmd, args,t)
    except KeyboardInterrupt:
        print("Type 'exit' to quit")
    except Exception as e:
        print(f"{t} error: {e}")





