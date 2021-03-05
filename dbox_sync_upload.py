import dropbox
import os
import sys
import shutil

from sh import rsync, gpg
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

from dbox_config import ROOT_BACKUP_DIR, SOURCE_ITEMS, GPG_ID, CURRENT_DATE

def make_encrypted_backup():
    """Making encrypted archive"""
    full_backup_dir = os.path.join(ROOT_BACKUP_DIR, CURRENT_DATE)
    remove_old_files(ROOT_BACKUP_DIR)
    os.mkdir(full_backup_dir)
    for item in SOURCE_ITEMS:
        rsync("-avrh", "--exclude=*.pyc", item, full_backup_dir)
    os.chdir(ROOT_BACKUP_DIR)
    shutil.make_archive(CURRENT_DATE, "zip", CURRENT_DATE)
    shutil.rmtree(CURRENT_DATE)
    arch_name = CURRENT_DATE + ".zip"
    gpg("-ear", GPG_ID, arch_name)


def push_to_dbox():
    """Uploads contents of LOCALFILE to Dropbox"""
    dbx = instantiate_dropbox()
    localfile = os.path.join(ROOT_BACKUP_DIR, CURRENT_DATE+".zip.asc")
    dbox_path = os.path.join('/source', os.path.split(localfile)[-1]) # Keep the forward slash before destination filename
    with open(localfile, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + localfile + " to Dropbox as " + dbox_path + "...")
        try:
            dbx.files_upload(f.read(), dbox_path, mode=WriteMode('overwrite'))
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
    source_list_files(dbx)


def source_list_files(dbox_instance):
    "Files list of destination DropBox folder"
    print("Files list:")
    for entry in dbox_instance.files_list_folder('/source').entries:
        print(entry.name)


def instantiate_dropbox():
    """ Make Dropbox instance"""
    token = os.environ.get("DBOX_TOKEN")
    if (len(token) == 0):
        sys.exit("ERROR: Looks like you didn't add your access token.")
    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(token)
    
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit(
            "ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    return dbx


def remove_old_files(temp_dir):
    """Removes all files in 'temp_dir' folder"""
    for file in os.listdir(temp_dir):
        full_file_path = os.path.join(temp_dir, file)
        try:
            os.unlink(full_file_path)
        except Exception as err:
            print(f'Failed to remove {full_file_path}. Reason: {err}')


if __name__ == '__main__':
    
    make_encrypted_backup()
    push_to_dbox()
