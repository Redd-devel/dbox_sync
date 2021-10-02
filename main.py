import sys
from shared_libs.dbox_sync_lib import download, upload


def main():
    if sys.argv[1] == "upload":
        upload()
    elif sys.argv[1] == "download":
        download()
    else:
        sys.exit(1)

# при синхроне на закачку лишние файлы должны удаляться

# заменить там где можно os.path на pathlib
