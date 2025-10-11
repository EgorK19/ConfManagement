from commands import parse_cmd, execute_cmd, log_event
from utils import get_uhd, get_username

def run_script(script_path, LOG_PATH=None):
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