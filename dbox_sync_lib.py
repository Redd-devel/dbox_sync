import dropbox
import os
import sys

from dropbox.exceptions import AuthError

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

def clean_dbox_folder(dbox_dir):
    """Removes all files in dbox_dir"""
    # need try except blocks!!!!!!!!!!
    dbx = instantiate_dropbox()
    for file in dbx.files_list_folder(dbox_dir).entries:
        dbx.files_delete_v2(file.path_display)