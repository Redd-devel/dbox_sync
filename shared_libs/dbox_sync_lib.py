import dropbox
import os
from pathlib import Path
import sys
import glob
import datetime
import shutil
from sh import rsync, gpg

from dropbox.exceptions import ApiError, AuthError
from shared_libs.dbox_config import WORK_DIR, SOURCE_ITEMS, \
                GPG_ID, CURRENT_DATE, RETENTION_PEROD


def upload_file(dbox_instance, dest_folder, dest_file):
    """Uploads content of backup files to Dropbox"""
    dbox_path = Path(dest_folder).joinpath(dest_file).__str__()
    with open(dest_file, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + dest_file + " to Dropbox as " + dbox_path + "...")
        try:
            dbox_instance.files_upload(f.read(), dbox_path, 
                mode=dropbox.files.WriteMode('overwrite'))
        except ApiError as err:
            # This checks for the specific error where a user doesn't have enough Dropbox space quota to upload this file
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


def download_file():
    """Download actual snapshot from Dropbox"""
    dbx = instantiate_dropbox()
    dbox_file = last_files_finder(dbx)
    filemask = Path(dbox_file).name
    destin_file = Path(WORK_DIR).joinpath(filemask).__str__()
    # print(destin_file)

    if not dbox_file:
        sys.exit("File doesn\'t exist")

    print("Downloading " + dbox_file + " to " + destin_file + "...")
    print(f'gpg -d -o {filemask[:23]} {filemask}')
    try:
        dbx.files_download_to_file(destin_file, dbox_file)
    except ApiError as err:
        print(err)
        sys.exit()
    os.chdir(WORK_DIR)
    gpg("-d", "-o", filemask[:23], filemask)

def instantiate_dropbox():
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
    return dbx

def clean_dbox_folder(dbox_instance, dbox_dir, days=RETENTION_PEROD):
    """Removes all files in dbox_dir"""
    time_diff = datetime.datetime.now() - datetime.timedelta(days=days)
    for file in dbox_instance.files_list_folder("/"+dbox_dir).entries:
            if file.server_modified < time_diff:
                print(f' File {file.path_display} be removed')
                try:
                    dbox_instance.files_delete_v2(file.path_display)
                except ApiError as err:
                    print(f'Something wrong with {file.path_display}. Reason: {err}')

def last_files_finder(dbox_obj):
    """Find last actual file"""
    days=0
    while days < 182:
        date_mask = (datetime.date.today() - \
            datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        filemask = "projects_" + date_mask + ".zip.asc"
        if dbox_obj.files_search("/projects", filemask).matches:
            return dbox_obj.files_search("/projects",
                filemask).matches[0].metadata.path_display
        days += 1
    return

def dbox_list_files(dbox_instance, dbox_dir, last=6):
    """Files list of destination DropBox folder"""
    print("Files list:")
    for entry in dbox_instance.files_list_folder(dbox_dir).entries[-last:]:
        print(entry.name)

def sync_entities():
    """Copy files, folders to destination"""
    source_list = SOURCE_ITEMS
    dbx = instantiate_dropbox()
    remove_old_files(WORK_DIR)
    relative_dirs = list(source_list.keys())
    for folder in relative_dirs:
        full_backup_dir = Path(WORK_DIR).joinpath(folder).__str__()
        for source_dir in source_list[folder]:
            rsync("-avrh", "--exclude=*.pyc", "--exclude=*.log*", "--exclude=.vscode", "--delete", source_dir, full_backup_dir) # "-R"
        # rsync("-avrh", "--exclude=*.pyc", "--exclude=*.log*", "--exclude=.vscode", "--delete", folder, full_backup_dir)
        encrypted_file = make_encrypted_files(folder)
        folder = "/" + folder
        upload_file(dbx, folder, encrypted_file)
        
        

def make_encrypted_files(path):
    """Make encrypted files"""
    os.chdir(WORK_DIR)
    base_file_name = path + '_' + CURRENT_DATE
    shutil.make_archive(base_file_name, "zip", path)
    arch_name = base_file_name + ".zip"
    gpg("-ear", GPG_ID, arch_name)
    return arch_name + ".asc"

def remove_old_files(temp_dir):
    """Removes all files in 'temp_dir' folder"""
    with os.scandir(temp_dir) as curr_dir:
        for item in curr_dir:
            if item.is_file():
                try:
                    os.unlink(item)
                except Exception as err:
                    print(f'Failed to remove {item}. Reason: {err}')
