import sys
from shared_libs.sync_lib import APIActions


def main():
    if sys.argv[1] == "upload":
        APIActions().upload()
    elif sys.argv[1] == "download":
        APIActions().download()
    else:
        print("error")
        sys.exit(1)

main()
