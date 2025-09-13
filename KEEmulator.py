import os
import sys

def get_uh_name():
    username = os.getlogin()
    hostname = (
        os.getenv('COMPUTERNAME', 'unknown')
        if os.name == 'nt'
        else getattr(os, 'uname', lambda: ('', 'unknown'))[1]
    )
    return f"{username}@{hostname}:~$ "

def parse_cmd(line):
    if not line.strip():
        return None, []

    parts = []
    i = 0
    n = len(line)
    current_arg = ''
    in_quotes = None

    while i < n:
        char = line[i]

        if in_quotes is None:
            if char.isspace():
                if current_arg:
                    parts.append(current_arg)
                    current_arg = ''
                i += 1
                continue
            elif char in '"\'':
                in_quotes = char
                i += 1
                continue
            else:
                current_arg += char
                i += 1
        else:
            if char == in_quotes:
                parts.append(current_arg)
                current_arg = ''
                in_quotes = None
                i += 1
            else:
                current_arg += char
                i += 1

    if current_arg:
        parts.append(current_arg)

    if not parts:
        return None, []

    return parts[0], parts[1:]

def execute_cmd(cmd, args):
    if cmd == 'exit':
        print("Exiting KEEmulator.")
        sys.exit(0)
    elif cmd == 'ls':
        print(f"ls {' '.join(args)}")
    elif cmd == 'cd':
        print(f"cd {' '.join(args)}")
    else:
        print(f"shell: command not found: {cmd}")

print("KEEmulator. Type 'exit' to quit.")
while True:
    try:
        line = input(get_uh_name())
        cmd, args = parse_cmd(line)
        if cmd:
            execute_cmd(cmd, args)
    except KeyboardInterrupt:
        print("\nUse 'exit' to quit.")
    except Exception as e:
        print(f"shell: error: {e}")