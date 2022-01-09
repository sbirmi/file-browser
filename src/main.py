import datetime
from flask import (
        Flask,
        render_template,
        request,
        send_file,
)
import os
import re
from werkzeug.utils import secure_filename

import Config
from Metadata import Store

app = Flask("file-browser")
app.config['UPLOAD_FOLDER'] = Config.upload_dir

def page(uploaded_files=[], failed_uploads=[],
        error="",
        message=""):
    udir = app.config["UPLOAD_FOLDER"]

    store = Store()
    file_data = store.get_db_data()

    file_data = [
            (fd.fname,
             fd.mime_type,
             fd.exif['FileSize'],
             fd.exif['FileModifyDate'],
             fd.exif_img_create_date,
             fd.deleted,
            ) for fd in file_data]

    return render_template("index.html",
            file_list=sorted(file_data),
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
    existing_fnames = {fd.fname for fd in store.get_db_data()}

    uploaded_files = request.files.getlist("files")
    for uploaded_file in uploaded_files:
        filename = secure_filename(uploaded_file.filename)

        if filename in existing_fnames:
            print("Duplicate detected", uploaded_file, filename)
            failed_uploads.append(filename)

        else:
            print("Uploaded:", uploaded_file, filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(local_path)
            store.process(local_path)
            success_files.append(filename)

    return page(
            uploaded_files=success_files,
            failed_uploads=failed_uploads)

@app.route("/thumbnail/<fname>")
def thumbnail(fname):
    thumb_file = os.path.join(Config.thumbnail_dir, fname)
    if os.path.exists(thumb_file):
        return send_file(thumb_file, mimetype="image")

    return "404"
