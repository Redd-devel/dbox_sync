import json
import requests
from dotenv import dotenv_values
import datetime

config = dotenv_values('.env')

def last_files_finder_rest(direct):
    """Find last actual file by rest api"""
    payload = {"options": {"path": f"/{direct}"}, "query": direct}
    payload_bin = json.dumps(payload)
    headers = {'Authorization': f'Bearer {config["DBOX_TOKEN"]}', 'Content-Type': 'application/json'}
    list_files_req = requests.post('https://api.dropboxapi.com/2/files/search_v2', headers=headers, data=payload_bin)
    days=0
    while days < 182:
        date_mask = (datetime.date.today() - \
            datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        filemask = f"{direct}_{date_mask}.zip.asc"
        for item in list_files_req.json()["matches"]:
            dbox_path = item["metadata"]["metadata"]["path_display"]
            if dbox_path.endswith(filemask):
                return dbox_path
        days += 1
    return
