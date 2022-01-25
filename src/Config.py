import os

metadata_file = "00_metadata.sqlite3"
upload_dir = "./uploads"
thumbnail_dir = "./thumbnails"

def upload_path(fname):
    return os.path.join(upload_dir, fname)

def thumbnail_path(fname):
    return os.path.join(thumbnail_dir, fname)

try:
    os.mkdir(upload_dir)
except:
    pass
try:
    os.mkdir(thumbnail_dir)
except:
    pass
