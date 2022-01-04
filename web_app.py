import json
from flask import Flask, render_template, request, flash
from libs.api_acts import APIActions
# from libs.dbox_config import single_dbox_inst

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)


dbox_obj = APIActions()
dbox_obj._dbx()

@app.route("/", methods=["POST", "GET"])
def index():
    # dbox_inst = dbox_obj._dbx()
    # dbox_inst = APIActions().instantiate_dropbox()
    dbox_dirs, dbox_files = dbox_obj.dbox_list_files("")
    if request.method == 'POST':
        selected_shelves = request.form.getlist('shelves')
        # print(selected_shelves)
        if request.form.get("upload") == "upload":
            try:
                dbox_obj.upload(selected_shelves)
                flash("Файлы успешно загружены", category='success')
            except Exception as err:
                flash("Что-то пошло не так", category='error')
                print("ERROR", err)
        elif request.form.get("download") == "download":
            sync_flag = True if request.form.get("sync") else False
            try:
                dbox_obj.download(selected_shelves, sync_flag)
                flash("Файлы успешно скачаны", category='success')
            except Exception as err:
                flash("Что-то пошло не так", category='error')
                print("ERROR", err)
    else:
        return render_template('index.html', dbox_dirs=dbox_dirs, dbox_files=dbox_files)
    return render_template('index.html', dbox_dirs=dbox_dirs, dbox_files=dbox_files)

if __name__ == '__main__':
    app.run()