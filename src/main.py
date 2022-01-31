import datetime
from flask import (
        Flask,
        jsonify,
        render_template,
        request,
        send_file,
)
import os
import re
from werkzeug.utils import secure_filename

import Config
from Metadata import Store
import Search
from Utils import ErrorResponse

app = Flask("file-browser")
app.config['UPLOAD_FOLDER'] = Config.upload_dir

def page(uploaded_files=[], failed_uploads=[],
        error="",
        message=""):
    udir = app.config["UPLOAD_FOLDER"]

    return render_template("index.html",
            error=error,
            message=message,
            failed_uploads=failed_uploads,
            failed_upload_count=len(failed_uploads),
            uploaded_files=uploaded_files)

@app.route('/')
def main():
    return page()

@app.route("/upload", methods=["POST"])
def upload():
    if 'files' not in request.files:
        return "No file(s) to upload"

    success_files = []
    failed_uploads = []

    store = Store()
    db_all_data = {fd.fname: fd for fd in store.get_db_data()}

    uploaded_files = request.files.getlist("files")
    for uploaded_file in uploaded_files:
        filename = secure_filename(uploaded_file.filename)

        db_row = db_all_data.get(filename)

        if not db_row or db_row.deleted:
            print("Uploaded:", uploaded_file, "->", filename)
            local_path = Config.upload_path(filename)
            uploaded_file.save(local_path)
            store.process(local_path)
            success_files.append(filename)

        else:
            print("Duplicate detected", uploaded_file, filename)
            failed_uploads.append(filename)

    return page(
            uploaded_files=success_files,
            failed_uploads=failed_uploads)

@app.route("/thumbnails/<fname>")
def thumbnail(fname):
    store = Store()
    thumb_file = Config.thumbnail_path(fname)
    if store.metadata.get('*', where={'thumbnail': fname}) and os.path.exists(thumb_file):
        return send_file(thumb_file, mimetype="image")

    return "404"

@app.route("/get/<fname>")
def get_file(fname):
    store = Store()
    upload_file = Config.upload_path(fname)
    if store.get_db_data_fname(fname) and os.path.exists(upload_file):
        return send_file(upload_file)#, mimetype="image")

    return "404"

@app.route("/db", methods=["GET"])
def db_data():
    """
    """
    args = request.args
    search = Search.Search(str(args.get('search', '')))
    if search.error_response:
        return search.error_response.serialize()
    start = args.get('start', '0')
    count = args.get('count', '50')

    try:
        start = int(start)
    except:
        return ErrorResponse("Bad start index")

    try:
        count = int(count)
    except:
        return ErrorResponse("Bad count")

    store = Store()
    filters = {"deleted": False}
    file_data = store.get_db_data(**filters)

    if search.filtering:
        file_data = [fd for fd in file_data if search.match(fd)]

    return jsonify(file_data[start:start + count])

@app.route("/db-stats", methods=["GET"])
def db_stats():
    store = Store()
    filters = {"deleted": False}

    return jsonify([
            Store.upload_dir_disk_usage(),
            store.metadata.count(where=filters)
        ])

@app.route("/update-tags", methods=["POST"])
def update_tags():
    if request.method != "POST":
        return jsonify(["ERROR", "GET not supported"])

    data = request.get_json()
    add_tags = data.get("add", [])
    remove_tags = data.get("remove", [])
    fnames = data.get("fnames", [])

    store = Store()
    return store.update_tags(fnames, add_tags, remove_tags).serialize()

@app.route("/tags", methods=["GET", "POST"])
def get_tags():
    store = Store()
    return jsonify(store.get_tags())
