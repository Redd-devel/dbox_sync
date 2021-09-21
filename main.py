import sys
from shared_libs.dbox_sync_lib import download_file, upload_file


def main():
    if sys.argv[1] == "upload":
        upload_file()
    elif sys.argv[1] == "download":
        download_file()
    else:
        sys.exit(1)
# синхрон файлов по папкам, архивация файлов по тематическим разделам, шифрование файлов
# загрузка на сервер, список загруженных файлов
# скачивание файлов, расшифровка файлов, разархивация файлов, синхрон с папками

# при синхроне на закачку лишние файлы должны удаляться


if __name__ == '__main__':
    main()