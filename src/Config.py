import os

root_dir = "./data"
metadata_file = os.path.join(root_dir, "00_metadata.sqlite3")
upload_dir = os.path.join(root_dir, "uploads")
thumbnail_dir = os.path.join(root_dir, "thumbnails")

def upload_path(fname):
    return os.path.join(upload_dir, fname)

def thumbnail_path(fname):
    return os.path.join(thumbnail_dir, fname)

try:
    os.system("mkdir -p " + upload_dir)
except:
    pass

try:
    os.system("mkdir -p " + thumbnail_dir)
except:
    pass
