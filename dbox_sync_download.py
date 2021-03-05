import dropbox
import os
import sys

from dropbox.exceptions import ApiError

from dbox_config import DOWNLOAD_DIR, CURRENT_DATE

def download_file():
    "Download actual snapshot from Dropbox"
    dbx = instantiate_dropbox()
    filemask = CURRENT_DATE + ".zip.asc"
    dbox_file = os.path.join('/source', filemask)
    destin_file = os.path.join(DOWNLOAD_DIR, filemask)

    checkFileDetails(filemask, dbx)

    print("Downloading " + dbox_file + " to " + destin_file + "...")
    try:
        dbx.files_download_to_file(destin_file, dbox_file)
    except ApiError as err:
        print(err)
        sys.exit()


def checkFileDetails(dbox_file, dbox_instance):
    "Check a necessary file in Dropbox"
    if len(dbox_instance.files_search('/source', dbox_file).matches) > 0:
        print(f'File {dbox_file} found')
    else:
        sys.exit(f'File {dbox_file} haven\'t found! Exit.')


def instantiate_dropbox():
    """Make Dropbox instance"""
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


if __name__ == '__main__':
    download_file()