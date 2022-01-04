import subprocess
import dropbox
import os
from pathlib import Path
import sys
from datetime import datetime, date, timedelta
import shutil
from dotenv import dotenv_values
from dropbox.exceptions import AuthError, ApiError

from libs.dbox_config import SOURCE_ITEMS, WORK_DIR, GPG_ID, \
                RETENTION_PEROD


class LocalActions:
    """Presents tools for FS works"""
    current_date = datetime.now().strftime("%Y-%m-%d")

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
            '--exclude=.git',
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
        base_file_name = path + '_' + self.current_date
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


class APIActions:
    # _dbx = instantiate_dropbox()

    def __init__(self) -> None:
        self._dbx = self.instantiate_dropbox
        # print("2nd time")
    
    def instantiate_dropbox(self):
        """ Make Dropbox instance"""
        token = os.environ.get("DBOX_TOKEN", '')
        if (len(token) == 0):
            sys.exit("ERROR: Looks like you didn't add your access token.")
        print("Creating a Dropbox object...")
        
        dbx = dropbox.Dropbox(token)
            
        try:
            dbx.users_get_current_account()
        except AuthError as err:
            print(err)
            sys.exit(
                "ERROR: Invalid access token; try re-generating \
                    an access token from the app console on the web.")
        print("1st time")
        return dbx


    fs_acts = LocalActions()
    current_date = datetime.now().strftime("%Y-%m-%d")

    def upload(self, shelves):
        """Copy files, folders to destination"""
        self.fs_acts.delete_old_project()
        for shelve in shelves:
            full_backup_dir = Path(WORK_DIR).joinpath(shelve).__str__()
            for source_dir in SOURCE_ITEMS[shelve]:
                self.fs_acts.sync_local_dirs(source_dir, full_backup_dir)
            encrypted_file = self.fs_acts.make_encrypted_files(shelve)
            shelve = "/" + shelve
            self.upload_file_to_cloud(shelve, encrypted_file)
        self.fs_acts.remove_old_files(WORK_DIR)

    def download(self, shelves, sync_ok):
        """Download actual snapshot from Dropbox"""
        config = dotenv_values('.env')
        for shelve in shelves:
            dbox_file = self.last_files_finder(shelve)
            if not dbox_file:
                sys.exit("File doesn\'t exist")
            shelve_dir = os.path.join(WORK_DIR, shelve)
            filemask = Path(dbox_file).name
            print(filemask)
            destin_file = os.path.join(WORK_DIR, shelve, filemask)
            os.chdir(shelve_dir)
            try:
                self.__dbx.files_download_to_file(destin_file, dbox_file)
            except ApiError as err:
                print(err)
                sys.exit()
            try:
                subprocess.run(
                ['gpg', '--pinentry-mode', 'loopback', 
                '--passphrase', config["GPG_PASS"], '--batch', '-d', '-o',
                os.path.splitext(filemask)[0], filemask]
            )
            except subprocess.CalledProcessError as err:
                print('ERROR: ', err)
            
            if sync_ok:
                # pass
                shutil.unpack_archive(os.path.splitext(filemask)[0])
                for destination in SOURCE_ITEMS[shelve]:
                    source = os.path.join(shelve_dir, os.path.basename(destination))
                    self.fs_acts.sync_local_dirs(source, os.path.dirname(destination))  
                self.fs_acts.remove_old_files(shelve_dir)

    
    
    def upload_file_to_cloud(self, dest_folder, dest_file):
        """Uploads content of backup files to Dropbox"""
        dbox_path = Path(dest_folder).joinpath(dest_file).__str__()
        with open(dest_file, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            print("Uploading " + dest_file + " to Dropbox as " + dbox_path + "...")
            try:
                self.__dbx.files_upload(f.read(), dbox_path, 
                    mode=dropbox.files.WriteMode('overwrite'))
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().error.is_insufficient_space()):
                    sys.exit("ERROR: Cannot back up; insufficient space.")
                elif err.user_message_text:
                    print(err.user_message_text)
                    sys.exit()
                else:
                    print(err)
                    sys.exit()
        self.clean_dbox_folder(dest_folder)
        # self.dbox_list_files(dest_folder)

    def clean_dbox_folder(self, dbox_dir, days=RETENTION_PEROD):
        """Removes all files in dbox_dir"""
        time_diff = datetime.now() - timedelta(days=days)
        for file in self.__dbx.files_list_folder("/"+dbox_dir).entries:
                if file.server_modified < time_diff:
                    print(f' File {file.path_display} be removed')
                    try:
                        self.__dbx.files_delete_v2(file.path_display)
                    except ApiError as err:
                        print(f'Something wrong with {file.path_display}. Reason: {err}')

    def last_files_finder(self, folder):
        """Find last actual file"""
        days=0
        while days < 182:
            date_mask = (date.today() - \
                timedelta(days=days)).strftime("%Y-%m-%d")
            filemask = f"{folder}_" + date_mask + ".zip.asc"
            if self.__dbx.files_search(f"/{folder}", filemask).matches:
                return self.__dbx.files_search(f"/{folder}",
                    filemask).matches[0].metadata.path_display
            days += 1
        return
    
    def arrive_cut(self, folders, files):
        separated_files_by_name = []
        for folder in folders:
            temp_list = []
            for file in files:
                if folder in file:
                    temp_list.append(file)
            separated_files_by_name.append(sorted(temp_list, reverse=True))
        return separated_files_by_name
    
    def dbox_list_files(self, dbox_dir):
        """Files list of destination DropBox folder"""
        files_list = []
        folders_list = []
        for entry in self._dbx.files_list_folder(dbox_dir, recursive=True).entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                folders_list.append(entry.name)
            else:
                files_list.append(entry.name)
        cut_files_list = self.arrive_cut(folders_list, files_list)
        return folders_list, cut_files_list
    
# def instantiate_dropbox():
#         """ Make Dropbox instance"""
#         token = os.environ.get("DBOX_TOKEN", '')
#         if (len(token) == 0):
#             sys.exit("ERROR: Looks like you didn't add your access token.")
#         print("Creating a Dropbox object...")
        
#         dbx = dropbox.Dropbox(token)
            
#         try:
#             dbx.users_get_current_account()
#         except AuthError as err:
#             print(err)
#             sys.exit(
#                 "ERROR: Invalid access token; try re-generating \
#                     an access token from the app console on the web.")
#         print("1st time")
#         return dbx

# single_dbox_inst = instantiate_dropbox()
