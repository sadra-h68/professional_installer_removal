import subprocess
import re
import os

def is_safe_name(name):
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', name))

def search_app_files(app_name):
    """فقط فایل‌های داخل دایرکتوری‌های استاندارد برنامه‌ها رو پیدا کن"""
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
                ['find', base, '-type', 'f', '-iname', f'*{app_name}*'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                results.extend([line for line in result.stdout.splitlines() if line])
        except subprocess.TimeoutExpired:
            continue
    return results

def uninstall_with_apt(package_name):
    """حذف بسته با apt"""
    cmd = ['sudo', 'apt', 'purge', '-y', package_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        subprocess.run(['sudo', 'apt', 'autoremove', '-y'], capture_output=True)
        return True, "حذف با apt موفق بود."
    else:
        return False, result.stderr

def safe_remove_path(path):
    """حذف امن یک مسیر (فقط اگر در مسیرهای مجاز باشد)"""
    allowed_prefixes = (
        '/usr/', '/etc/', '/var/', '/opt/', '/home/'
    )
    if not any(path.startswith(p) for p in allowed_prefixes):
        return False, "مسیر غیرمجاز"

    if not os.path.exists(path):
        return True, "فایل وجود ندارد"

    try:
        if os.path.islink(path) or os.path.isfile(path):
            subprocess.run(['sudo', 'rm', '-f', path], check=True)
        elif os.path.isdir(path):
            subprocess.run(['sudo', 'rm', '-rf', path], check=True)
        return True, "حذف شد"
    except Exception as e:
        return False, str(e)

# ———— اجرای اصلی ————
if __name__ == "__main__":
    raw_input = input("enter the app name:\t").strip()
    
    if not raw_input or not is_safe_name(raw_input):
        print("نام برنامه نامعتبر است!")
        exit(1)

    app_name = raw_input
    print("در حال جستجو و حذف...")

    # ۱. حذف با apt
    apt_success, apt_msg = uninstall_with_apt(app_name)
    if apt_success:
        print('\033[92m' + "حذف با apt کامل شد." + '\033[0m')
    else:
        print('\033[93m' + f"apt نتوانست حذف کند: {apt_msg}" + '\033[0m')

    # ۲. جستجوی فایل‌های باقی‌مانده
    remaining_files = search_app_files(app_name)
    if not remaining_files:
        print("هیچ فایل باقی‌مانده‌ای پیدا نشد.")
    else:
        print(f"تعداد {len(remaining_files)} فایل باقی‌مانده پیدا شد:")
        for path in remaining_files:
            print(f"  → \033[93m{path}\033[0m")
            success, msg = safe_remove_path(path)
            if success:
                print(f"    \033[92mحذف شد\033[0m")
            else:
                print(f"    \033[91mخطا: {msg}\033[0m")

    print("\nعملیات پایان یافت.")