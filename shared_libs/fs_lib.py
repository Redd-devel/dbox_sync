import os
import shutil
# from shared_libs.dbox_config import SOURCE_ITEMS, WORK_DIR
from dbox_config import SOURCE_ITEMS, WORK_DIR



def delete_old_project():
    """Removes unactual projects from backup folder"""
    for item in SOURCE_ITEMS.keys():
        os.chdir(os.path.join(WORK_DIR, item))
        fs_list_dirs = os.listdir()
        print(fs_list_dirs)
        for synced_dir in SOURCE_ITEMS[item]:
            print(os.path.basename(synced_dir))
            fs_list_dirs.remove(os.path.basename(synced_dir))
            print(fs_list_dirs)
        for dir_to_remove in fs_list_dirs:
            try:
                shutil.rmtree(dir_to_remove)
            except OSError as err:
                print(f'Cannot remove {dir_to_remove}. Error {err}')


if __name__ == '__main__':
    delete_old_project()