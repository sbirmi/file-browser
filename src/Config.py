import os

upload_dir = "./uploads"
thumbnail_dir = "./thumbnails"

def upload_path(fname):
    return os.path.join(upload_dir, fname)

def thumbnail_path(fname):
    return os.path.join(thumbnail_dir, fname)
