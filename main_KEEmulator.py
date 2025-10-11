from utils import setup_args, setup_logging, get_username, get_uhd
import vfs
from commands import parse_cmd, execute_cmd, log_event
from script_runner import run_script

VFS_PATH = None
LOG_PATH = None
SCRIPT_PATH = None

args = setup_args()

VFS_PATH = args.vfs_path
LOG_PATH = args.log_path
SCRIPT_PATH = args.script_path

print("Launch parameters received:")
print(f"\tVFS_PATH: {VFS_PATH}")
print(f"\tLOG_PATH: {LOG_PATH}")
print(f"\tSCRIPT_PATH: {SCRIPT_PATH}")

if LOG_PATH:
    setup_logging(LOG_PATH)

if VFS_PATH:
    if vfs.load_vfs(VFS_PATH):
        print("VFS loaded successfully")
    else:
        print("Failed to load VFS")

if SCRIPT_PATH:
    run_script(SCRIPT_PATH, LOG_PATH)

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
# python main_KEEmulator.py --vfs_path=simpleVFS.json --log_path=emulator.log --script_path=script1.txt

# Расширенная VFS
# python main_KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=script2.txt

# Полный тест
# python main_KEEmulator.py --vfs_path=advancedVFS.json --log_path=emulator.log --script_path=test_script.txt