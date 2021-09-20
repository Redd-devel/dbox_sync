import os
import sys

from dropbox.exceptions import ApiError
from dbox_config import DOWNLOAD_DIR
from dbox_sync_lib import instantiate_dropbox, last_files_finder

def download_file():
    """Download actual snapshot from Dropbox"""
    dbx = instantiate_dropbox()
    dbox_file = last_files_finder()
    filemask = os.path.basename(dbox_file)
    destin_file = os.path.join(DOWNLOAD_DIR, filemask)

    if not dbox_file:
        sys.exit("File doesn\'t exist")

    print("Downloading " + dbox_file + " to " + destin_file + "...")
    try:
        dbx.files_download_to_file(destin_file, dbox_file)
    except ApiError as err:
        print(err)
        sys.exit()


if __name__ == '__main__':
    download_file()