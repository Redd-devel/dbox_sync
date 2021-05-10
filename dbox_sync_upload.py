import dropbox
import os
import sys
import shutil

from sh import rsync, gpg
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError

from dbox_config import ROOT_BACKUP_DIR, SOURCE_ITEMS, GPG_ID, CURRENT_DATE, DBOX_FOLDER
from dbox_sync_lib import instantiate_dropbox, collect_files


def sync_entities(source_list):
    """Copy files, folders to destination"""
    remove_old_files(ROOT_BACKUP_DIR)
    relative_dirs = list(source_list.keys())
    for folder in relative_dirs:
        full_backup_dir = os.path.join(ROOT_BACKUP_DIR, folder)
        for item in source_list[folder]:
            rsync("-avrh", "--exclude=*.pyc", "--exclude=*.log*", "--exclude=.vscode", "--delete", item, full_backup_dir) # "-R"
        make_encrypted_files(folder)

def make_encrypted_files(path):
    """Make encrypted files"""
    os.chdir(ROOT_BACKUP_DIR)
    base_file_name = path + '_' + CURRENT_DATE
    shutil.make_archive(base_file_name, "zip", path)
    arch_name = base_file_name + ".zip"
    gpg("-ear", GPG_ID, arch_name)

def push_to_dbox():
    """Uploads content of backup files to Dropbox"""
    dbx = instantiate_dropbox()
    for item in collect_files('*.asc'):
        dbox_path = os.path.join(DBOX_FOLDER, item) # Keep the forward slash before destination filename
        with open(item, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            print("Uploading " + item + " to Dropbox as " + dbox_path + "...")
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
    dest_list_files(dbx)


def dest_list_files(dbox_instance):
    "Files list of destination DropBox folder"
    print("Files list:")
    for entry in dbox_instance.files_list_folder(DBOX_FOLDER).entries:
        print(entry.name)


def remove_old_files(temp_dir):
    """Removes all files in 'temp_dir' folder"""
    with os.scandir(temp_dir) as curr_dir:
        for item in curr_dir:
            if item.is_file():
                try:
                    os.unlink(item)
                except Exception as err:
                    print(f'Failed to remove {item}. Reason: {err}')


if __name__ == '__main__':
    sync_entities(SOURCE_ITEMS)
    push_to_dbox()
