import dropbox
import os
import sys
import glob

from dropbox.exceptions import ApiError, AuthError

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
        sys.exit(
            "ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    return dbx

def clean_dbox_folder(dbox_dir):
    """Removes all files in dbox_dir"""
    dbx = instantiate_dropbox()
    for file in dbx.files_list_folder(dbox_dir).entries:
        try:
            dbx.files_delete_v2(file.path_display)
        except ApiError as err:
            print(f'Something wrong with {file.path_display}. Reason: {err}')

def collect_files(filemask: str) -> list():
    """Collect files by a mask"""
    return glob.glob(filemask)
