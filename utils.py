import os
import logging

def setup_args():
    import argparse
    parser = argparse.ArgumentParser(description='KEEmulator')
    parser.add_argument('--vfs_path', type=str, help='Path to VFS physical location')
    parser.add_argument('--log_path', type=str, help='Path to log file')
    parser.add_argument('--script_path', type=str, help='Path to startup script')
    return parser.parse_args()

def setup_logging(log_path):
    logging.basicConfig(
        filename=log_path,
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
    import vfs
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

    if vfs.vfs_root:
        cwd = '/' + '/'.join(vfs.current_vfs_path)
    else:
        cwd = os.getcwd()
        dir = os.path.expanduser('~')
        if cwd.startswith(dir):
            cwd = '~' + cwd[len(dir):]

    return f"{username}@{hostname}:{cwd}$ "
