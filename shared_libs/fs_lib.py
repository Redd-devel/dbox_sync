import os
import shutil
import subprocess
from shared_libs.dbox_config import SOURCE_ITEMS, WORK_DIR


def delete_old_project():
    """Removes unactual projects from backup folder"""
    for item in SOURCE_ITEMS.keys():
        os.chdir(os.path.join(WORK_DIR, item))
        fs_list_dirs = os.listdir()
        for synced_dir in SOURCE_ITEMS[item]:
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
        '--delete',
        source,
        dest
    ]
    try:
        subprocess.check_call(subprocess_args)
    except subprocess.CalledProcessError as err:
        print('PRINT:', err)


if __name__ == '__main__':
    delete_old_project()