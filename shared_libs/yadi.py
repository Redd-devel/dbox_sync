import yadisk
from dotenv import dotenv_values
#from shared_libs.dbox_config import WORK_DIR, SOURCE_ITEMS, RETENTION_PEROD

# https://yadisk.readthedocs.io/ru/latest/intro.html documentation

def yad_upload():
    pass

def yad_instance():
    """Create Yandex disk instance"""
    config = dotenv_values('.env')
    token = yadisk.YaDisk(token=config["YA_TOKEN"])
    if (token.check_token()):
        return token
    return None


if __name__ == "__main__":
    yad_instance()