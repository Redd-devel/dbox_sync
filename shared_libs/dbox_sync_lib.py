import dropbox
import os
import sys
import glob
import datetime

from dropbox.exceptions import ApiError, AuthError
from dbox_config import DBOX_FOLDER

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

def collect_files(filemask: str) -> list:
    """Collect files by a mask"""
    return glob.glob(filemask)

def last_files_finder():
    """Find last actual file"""
    dbx = instantiate_dropbox()
    days=0
    while days < 182:
        date_mask = (datetime.date.today() - \
            datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        filemask = "projects_" + date_mask + ".zip.asc"
        if dbx.files_search(DBOX_FOLDER, filemask).matches:
            return dbx.files_search(DBOX_FOLDER, filemask).matches[0].metadata.path_display
        days += 1
    return

if __name__ == '__main__':
    print(last_files_finder())
