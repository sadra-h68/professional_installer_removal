import subprocess
import re
import os

def is_safe_name(name):
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', name))

def search_app_paths(app_name):
    safe_paths = [
        '/usr/bin', '/usr/sbin',
        '/usr/lib', '/usr/libexec',
        '/usr/share', '/etc',
        '/var/lib', '/opt',
        '/home'
    ]
    results = []
    for base in safe_paths:
        if not os.path.exists(base):
            continue
        try:
            result = subprocess.run(
                ['find', base, '-iname', f'*{app_name}*'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                results.extend(lines)
        except subprocess.TimeoutExpired:
            continue
    return results

def safe_remove_path(path):
    allowed_prefixes = (
        '/usr/', '/etc/', '/var/', '/opt/', '/home/'
    )
    if not any(path.startswith(p) for p in allowed_prefixes):
        return False, "Unauthorized route"

    if not os.path.exists(path):
        return True, "not found"

    try:
        if os.path.islink(path) or os.path.isfile(path):
            subprocess.run(['sudo', 'rm', '-f', path], check=True)
            return True, "file deleted"
        elif os.path.isdir(path):
            subprocess.run(['sudo', 'rm', '-rf', path], check=True)
            return True, "dir deleted"
        return False, "Unspecified type"
    except Exception as e:
        return False, f"خطا: {str(e)}"

def uninstall_with_apt(package_name):
    cmd = ['sudo', 'apt', 'purge', '-y', package_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        subprocess.run(['sudo', 'apt', 'autoremove', '-y'], capture_output=True)
        return True, "apt: complated removing"
    else:
        return False, f"apt: {result.stderr.strip()}"

if __name__ == "__main__":
    raw_input = input("enter the app name:\t").strip()
    
    if not raw_input or not is_safe_name(raw_input):
        print("The application name is invalid!")
        exit(1)

    app_name = raw_input
    print(f"Deleting '{app_name}'...")

    apt_success, apt_msg = uninstall_with_apt(app_name)
    print('\033[92m' + apt_msg + '\033[0m' if apt_success else '\033[93m' + apt_msg + '\033[0m')

    paths = search_app_paths(app_name)
    if not paths:
        print("No files or folders found.")
    else:
        print(f"Item found: {len(paths)}")
        
        files = [p for p in paths if os.path.isfile(p) or os.path.islink(p)]
        dirs = [p for p in paths if os.path.isdir(p)]
        dirs.sort(key=lambda x: len(x.split('/')), reverse=True)  

        for path in files:
            print(f"  [F] \033[93m{path}\033[0m", end=" → ")
            success, msg = safe_remove_path(path)
            print('\033[92m deleted \033[0m' if success else f'\033[91m{msg}\033[0m')

        for path in dirs:
            print(f"  [D] \033[93m{path}\033[0m", end=" → ")
            success, msg = safe_remove_path(path)
            print('\033[92m deleted \033[0m' if success else f'\033[91m{msg}\033[0m')

    print("\ncomplated")