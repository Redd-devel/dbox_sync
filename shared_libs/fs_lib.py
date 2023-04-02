import os
import shutil
import subprocess
from .dbox_config import WORK_DIR, CURRENT_DATE
from .conf_parser import readConfig, path_reconciler
from dotenv import dotenv_values


SOURCE_ITEMS = readConfig(path_reconciler())
config = dotenv_values(".env")


def delete_old_project(folder):
    """Removes unactual projects from backup folder"""
    os.chdir(os.path.join(WORK_DIR, folder))
    fs_list_dirs = os.listdir()
    for synced_dir in SOURCE_ITEMS[folder]:
        try:
            fs_list_dirs.remove(os.path.basename(synced_dir))
        except ValueError:
            continue
    if not fs_list_dirs:
        return
    for dir_to_remove in fs_list_dirs:
        try:
            shutil.rmtree(dir_to_remove)
        except OSError as err:
            print(f'Cannot remove {dir_to_remove}. Error {err}')

def sync_local_dirs(source, dest):
    """Synchronizes 2 folders"""
    subprocess_args = [
        'rsync', '-avrh',
        '--exclude=*.pyc',
        '--exclude=*.log*',
        '--exclude=.vscode',
        '--exclude=.git',
        '--exclude=dbox_config.py',
        '--delete',
        source,
        dest
    ]
    try:
        subprocess.check_call(subprocess_args)
    except subprocess.CalledProcessError as err:
        print('PRINT:', err)

def remove_old_files(temp_dir):
    """Removes all files in 'temp_dir' folder"""
    # reviewed
    with os.scandir(temp_dir) as curr_dir:
        for item in curr_dir:
            if item.is_file():
                try:
                    os.unlink(item)
                except Exception as err:
                    print(f'Failed to remove {item}. Reason: {err}')

def make_encrypted_files(path):
    """Make encrypted files"""
    # reviewed
    os.chdir(WORK_DIR)
    base_file_name = path + '_' + CURRENT_DATE
    try:
        shutil.make_archive(base_file_name, "zip", path)
    except Exception as err:
        print('ERROR:', err)
    arch_name = base_file_name + ".zip"
    try:
        subprocess.run(['gpg', '-ear', config["GPG_ID"], arch_name])
    except subprocess.CalledProcessError as err:
        print('ERROR:', err)
    return arch_name + ".asc"


def check_gpg_key() -> bool:
    """Check gpg_id"""
    retval = subprocess.run(["gpg", "-k"], stdout=subprocess.PIPE, encoding='utf-8')
    if config["GPG_ID"] not in retval.stdout:
        print("There is no target key or gnupg is not installed. Program aborted")
        return False
    return True

def keys_list() -> list:
    return list(SOURCE_ITEMS.keys())

def check_dir(folder: str) -> None:
    """Check existing directory"""
    if not os.path.isdir(folder):
        os.mkdir(folder)
        print(f'{folder} created')
    else:
        os.chdir(folder)

if __name__ == '__main__':
    # delete_old_project()
    check_gpg_key()