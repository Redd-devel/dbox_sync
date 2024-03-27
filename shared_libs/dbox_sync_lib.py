import subprocess
import dropbox
import yadisk
import os
from pathlib import Path
import sys
import datetime
import shutil
from dotenv import dotenv_values
import pytz

from dropbox.exceptions import ApiError, AuthError
from yadisk.exceptions import YaDiskError
# from .dbox_config import SOURCE_ITEMS, WORK_DIR, CURRENT_DATE
from .dbox_config import WORK_DIR, RETENTION_PERIOD
from .conf_parser import readConfig, path_reconciler
from .fs_lib import delete_old_project, sync_local_dirs, remove_old_files, make_encrypted_files, keys_list, check_dir, check_gpg_key
from .rest_api import last_files_finder_rest

__all__ = ["download", "upload"]

SOURCE_ITEMS = readConfig(path_reconciler())
print(SOURCE_ITEMS)
config = dotenv_values('.env')

def upload():
    """Copy files, folders to destination"""
    # need refactoring
    if not check_gpg_key:
        sys.exit()
    dbx = instantiate_dropbox()
    yad = yad_instance()
    for folder in keys_list():
        delete_old_project(folder)
        full_backup_dir = Path(WORK_DIR).joinpath(folder).__str__()
        for source_dir in SOURCE_ITEMS[folder]:
            sync_local_dirs(source_dir, full_backup_dir)
        encrypted_file = make_encrypted_files(folder)
        upload_file_to_cloud(dbx, f'/{folder}', encrypted_file)
        upload_file_to_cloud_ya(yad, f'/{folder}', encrypted_file)
    remove_old_files(WORK_DIR)

def download():
    """Download actual snapshot from Dropbox"""
    # reviewed
    if not check_gpg_key:
        sys.exit()
    dbx = instantiate_dropbox()
    for item in keys_list():
        dbox_file = last_files_finder_rest(item)
        if not dbox_file:
            continue
        filemask = Path(dbox_file).name
        zipfile_mask = os.path.splitext(filemask)[0]
        destin_file = os.path.join(WORK_DIR, item, filemask)
        print("Downloading " + dbox_file + " to " + destin_file + "...")
        item_dir = os.path.join(WORK_DIR, item)
        check_dir(item_dir)
        try:
            dbx.files_download_to_file(destin_file, dbox_file)
        except ApiError as err:
            print(f'ERROR: {err}')
        try:
            subprocess.run(
            ['gpg', '--pinentry-mode', 'loopback', 
            '--passphrase', config["GPG_PASS"], '--batch', '-d', '-o',
            zipfile_mask, filemask]
        )
        except subprocess.CalledProcessError as err:
            print(f'ERROR: {err}')
        shutil.unpack_archive(zipfile_mask)
        for destination in SOURCE_ITEMS[item]:
            source = os.path.join(item_dir, os.path.basename(destination))
            sync_local_dirs(source, os.path.dirname(destination))
        remove_old_files(item_dir)

def instantiate_dropbox():
    """ Make Dropbox instance"""
    # reviewed
    # token = os.environ.get("DBOX_TOKEN", '')
    token = config["DBOX_TOKEN"]
    if (len(token) == 0):
        sys.exit("ERROR: Looks like your access token is empty.")
    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(token)
    
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        print("ERROR: Invalid access token; try re-generating \
                an access token from the app console on the web.", err)
    return dbx

def upload_file_to_cloud(dbox_instance, dest_folder, dest_file):
    """Uploads content of backup files to Dropbox"""
    # reviewed, but pay attention to exception handling
    dbox_path = Path(dest_folder).joinpath(dest_file).__str__()
    with open(dest_file, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + dest_file + " to Dropbox as " + dbox_path + "...")
        try:
            dbox_instance.files_upload(f.read(), dbox_path, 
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
    clean_dbox_folder(dbox_instance, dest_folder)
    dbox_list_files(dbox_instance, dest_folder)

def clean_dbox_folder(dbox_instance, dbox_dir, days=RETENTION_PERIOD):
    """Removes all files in dbox_dir"""
    # reviewed
    time_diff = datetime.datetime.now() - datetime.timedelta(days=days)
    for file in dbox_instance.files_list_folder("/"+dbox_dir).entries:
            if file.server_modified < time_diff:
                print(f' File {file.path_display} be removed')
                try:
                    dbox_instance.files_delete_v2(file.path_display)
                except ApiError as err:
                    print(f'Something wrong with {file.path_display}. Reason: {err}')

def last_files_finder(dbox_instance, direct):
    """Find last actual file"""
    # 
    days=0
    while days < 182:
        date_mask = (datetime.date.today() - \
            datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        # for item in keys_list():
            # filemask = item + "_" + date_mask + ".zip.asc"
        filemask = f"{direct}_{date_mask}.zip.asc"
        if dbox_instance.files_search(f"/{direct}", filemask).matches:
            return dbox_instance.files_search(f"/{direct}",
                filemask).matches[0].metadata.path_display
        days += 1
    return

#----------------
def last_files_finder_dev(dbox_instance, direct):
    """Find last actual file"""
    # 
    days=0
    while days < 182:
        date_mask = (datetime.date.today() - \
            datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        # for item in keys_list():
            # filemask = item + "_" + date_mask + ".zip.asc"
        filemask = f"{direct}_{date_mask}.zip.asc"
        # print(filemask)
        print(dbox_instance.files_search(f"/{direct}", f"{direct}_20"))
        break
        files_array = dbox_instance.files_search(f"/{direct}", f"{direct}_20").matches
        for item in files_array:
            print(item.metadata.path_display)
            if item.metadata.path_display.endswith(filemask):
                return item.metadata.path_display
        days += 1
    return
#----------------

def dbox_list_files(dbox_instance, dbox_dir, last=6):
    """Files list of destination DropBox folder"""
    # reviewed
    print(f'Last {last} files list:')
    for entry in dbox_instance.files_list_folder(dbox_dir).entries[-last:]:
        print(entry.name)



def upload_file_to_cloud_ya(yad_instan, dest_folder, dest_file):
    yad_path = os.path.join("/", dest_folder, dest_file)
    with open(dest_file, "rb") as file:
        yad_instan.upload(file, yad_path, overwrite=True)
    clean_ya_folder(yad_instan, dest_folder)
    yad_list_files(yad_instan, dest_folder)

def yad_instance():
    """Create Yandex disk instance"""
    # config = dotenv_values('.env')
    yad_inst = yadisk.YaDisk(token=config["YA_TOKEN"])
    # yad_inst = yadisk.YaDisk(token=os.environ.get("YA_DISK_TOKEN", ''))
    if not (yad_inst.check_token()):
        print("Token is invalid")
        sys.exit(1)
    print("Yandex Disk instance successfully created!")
    return yad_inst

def clean_ya_folder(yad_instance, yad_dir, days=RETENTION_PERIOD):
    """Clean yandex folder"""
    time_diff = datetime.datetime.now() - datetime.timedelta(days=days)
    for file in list(yad_instance.listdir(yad_dir)):
        if file.created < time_diff.replace(tzinfo=pytz.utc):
            print(f' File {file.name} be removed')
            try:
                yad_instance.remove(file.path)
            except YaDiskError as err:
                print(f'Something wrong with {file.path}. Reason: {err}')

def yad_list_files(yad_instance, yad_dir, last=6):
    """Files list of destination YaDisk folder"""
    print(f'Last {last} files list:')
    for entry in list(yad_instance.listdir(yad_dir))[-last:]:
        print(entry.name)
