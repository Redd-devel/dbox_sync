import subprocess
import dropbox
import os
from pathlib import Path
import sys
import datetime
import shutil
from dotenv import dotenv_values

from dropbox.exceptions import ApiError, AuthError
from shared_libs.dbox_config import WORK_DIR, SOURCE_ITEMS, RETENTION_PEROD
from shared_libs.fs_lib import delete_old_project, sync_local_dirs, remove_old_files, make_encrypted_files, keys_list, check_dir, check_gpg_key


def upload():
    """Copy files, folders to destination"""
    # need refactoring
    if not check_gpg_key:
        sys.exit()
    dbx = instantiate_dropbox()
    for folder in keys_list():
        delete_old_project(folder)
        full_backup_dir = Path(WORK_DIR).joinpath(folder).__str__()
        for source_dir in SOURCE_ITEMS[folder]:
            sync_local_dirs(source_dir, full_backup_dir)
        encrypted_file = make_encrypted_files(folder)
        upload_file_to_cloud(dbx, f'/{folder}', encrypted_file)
    remove_old_files(WORK_DIR)

def download():
    """Download actual snapshot from Dropbox"""
    # reviewed
    if not check_gpg_key:
        sys.exit()
    dbx = instantiate_dropbox()
    config = dotenv_values('.env')
    for item in keys_list():
        dbox_file = last_files_finder(dbx, item)
        if not dbox_file:
            continue
        filemask = Path(dbox_file).name
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
            filemask[-1:-5:-1], filemask]
        )
        except subprocess.CalledProcessError as err:
            print(f'ERROR: {err}')
        shutil.unpack_archive(filemask[-1:-5:-1])
        for destination in SOURCE_ITEMS[item]:
            source = os.path.join(item_dir, os.path.basename(destination))
            sync_local_dirs(source, os.path.dirname(destination))
        remove_old_files(item_dir)

def instantiate_dropbox():
    """ Make Dropbox instance"""
    # reviewed
    token = os.environ.get("DBOX_TOKEN", '')
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

def clean_dbox_folder(dbox_instance, dbox_dir, days=RETENTION_PEROD):
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

def dbox_list_files(dbox_instance, dbox_dir, last=6):
    """Files list of destination DropBox folder"""
    # reviewed
    print(f'Last {last} files list:')
    for entry in dbox_instance.files_list_folder(dbox_dir).entries[-last:]:
        print(entry.name)
