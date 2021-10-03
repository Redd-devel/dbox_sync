import sys
from shared_libs.dbox_sync_lib import download, upload


def main():
    if sys.argv[1] == "upload":
        upload()
    elif sys.argv[1] == "download":
        download()
    else:
        print("error")
        sys.exit(1)

main()
