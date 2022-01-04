# Dropbox Upload/Download utility

## Short description

There are two python scripts for interacting with Dropbox API

**dbox_sync_lib.py** - 

## Prerequisites

Debian-like operating systems.

You need to install rsync and gpg: `sudo apt install rsync gpg`

Python 3.5+

All the necessary python packages are in requirements.txt.

## Getting Dropbox token

1. Go to <https://www.dropbox.com/developers> and create a new App
2. Set a name for your app
3. Set the following permissions on the `Permissions` tab: account_info.write, files_content.write, files.content.read
4. Set `Access token expiration` to `No expiration`
5. Generate token on the `Settings` tab
6. Copy the token in a secure place

I use an environment variable keep token:
`export DBOX_TOKEN='tttoookkkeeennn'`

## Config file

`dbox_config.py`:

```
from datetime import datetime

GPG_ID = 'email@email.com'
SOURCE_ITEMS = {
    'projects': ('/some/folder','/some/file.ext',),
    'custom': ('/some/custom/folder','/some/custom/file.ext',)
}
WORK_DIR = '/download/folder'
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
DBOX_FOLDER = '/folder'
```
