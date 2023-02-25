import argparse
from shared_libs import download, upload

parser = argparse.ArgumentParser(description='DropBox and Yandex clouds executor')
parser.add_argument('action', type=str, help='Choose an action', choices=['upload', 'dowload'])

args = parser.parse_args()

def main():
    if args.action == "upload":
        upload()
    elif args.action == "download":
        download()

main()
