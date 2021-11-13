import os
import shutil
import subprocess
from shared_libs.dbox_config import SOURCE_ITEMS, WORK_DIR, GPG_ID, CURRENT_DATE

# def delete_old_project():
#     """Removes unactual projects from backup folder"""
#     for item in SOURCE_ITEMS.keys():
#         os.chdir(os.path.join(WORK_DIR, item))
#         fs_list_dirs = os.listdir()
#         for synced_dir in SOURCE_ITEMS[item]:
#             try:
#                 fs_list_dirs.remove(os.path.basename(synced_dir))
#             except ValueError:
#                 continue
#         if not fs_list_dirs:
#             return
#         for dir_to_remove in fs_list_dirs:
#             try:
#                 shutil.rmtree(dir_to_remove)
#             except OSError as err:
#                 print(f'Cannot remove {dir_to_remove}. Error {err}')


# def sync_local_dirs(source, dest):
#     """Synchronizes 2 folders"""
#     subprocess_args = [
#         'rsync', '-avrh',
#         '--exclude=*.pyc',
#         '--exclude=*.log*',
#         '--exclude=.vscode',
#         '--delete',
#         source,
#         dest
#     ]
#     try:
#         subprocess.check_call(subprocess_args)
#     except subprocess.CalledProcessError as err:
#         print('PRINT:', err)


class LocalActions:
    """Presents tools for FS works"""   
    def delete_old_project(self):
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


    def sync_local_dirs(self, source, dest):
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
    
    def make_encrypted_files(self, path):
        """Make encrypted files"""
        os.chdir(WORK_DIR)
        base_file_name = path + '_' + CURRENT_DATE
        shutil.make_archive(base_file_name, "zip", path)
        arch_name = base_file_name + ".zip"
        try:
            subprocess.run(['gpg', '-ear', GPG_ID, arch_name])
        except subprocess.CalledProcessError as err:
            print('ERROR:', err)
        return arch_name + ".asc"


    def remove_old_files(self, temp_dir):
        """Removes all files in 'temp_dir' folder"""
        with os.scandir(temp_dir) as curr_dir:
            for item in curr_dir:
                if item.is_file():
                    try:
                        os.unlink(item)
                    except Exception as err:
                        print(f'Failed to remove {item}. Reason: {err}')
