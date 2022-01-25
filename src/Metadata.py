from contextlib import contextmanager
import json
import os
import sqlite3
import subprocess
import tempfile

from HashLib import hash_sha256

import Config
from Storage import (
        Bool,
        Int,
        Json,
        Table,
        Timestamp,
        Txt,
)
from Utils import (
        check_output,
        now,
        run,
        trace,
)

class ExifApi():
    def get_info(self, path):
        cmd = ["exiftool", "-n", "-json", path]
        trace(cmd)
        output = subprocess.check_output(cmd)
        jdata = json.loads(output)[0]
        return jdata

exif_api = ExifApi()

class Metadata(Table):
    fields = [
            Txt("fname"),
            Txt("hash_sha256"),
            Timestamp("time_db_added"),
            Timestamp("time_db_updated"),
            Bool("deleted"),
            Txt("desc"),
            Json("exif"), # exiftool -json data
            Txt("mime_type"),
            Timestamp("exif_img_create_date"),
            Txt("thumbnail"),
        ]

class Store():
    def __init__(self, fname=Config.metadata_file):
        self.fname = fname
        self.conn = sqlite3.connect(self.fname)
        self.cursor = self.conn.cursor()
        self.metadata = Metadata(self.cursor)

        self.commit_ctx_depth = 0
        self.commit()

    @staticmethod
    def upload_dir_disk_usage():
        cmd = ["du", "-sh", Config.upload_dir.rstrip("/") + "/"]
        output = subprocess.check_output(cmd)
        # Sample output
        # 4.4G    uploads/
        return output.split()[0].decode("utf-8")

    @staticmethod
    def samefile(path, fname, exif, existing_data):
        if not existing_data and not exif:
            return True
        assert existing_data and exif

        col_idxs = Metadata.column_idxs()
        metadata_exif = existing_data[col_idxs['exif']]

        return metadata_exif['FileSize'] == exif['FileSize'] and \
                metadata_exif['FileModifyDate'] == exif['FileModifyDate'] and \
            existing_data[col_idxs['hash_sha256']] == hash_sha256(path)

    @staticmethod
    def mime_type(path):
        cmd = ["file", "-b", "--mime-type", path]
        output = subprocess.check_output(cmd).decode("utf8")
        return output

    @staticmethod
    def video_frame(path):
        tmppath = tempfile.mktemp()
        cmd = ["ffmpeg", "-i", path, "-r", "1", "-v", "quiet", "-t", "00:00:01", "-f", "image2", tmppath]
        result = run(cmd)
        if result is None:
            return None
        return tmppath

    @staticmethod
    def video_duration(path):
        cmd = ["ffprobe", "-i", path, "-show_entries", "format=duration", "-v", "quiet", "-of", 'csv=p=0']
        output = check_output(cmd)
        # Sample output: '10.508333\n'
        if not output:
            return None
        text = output.split()[0]
        if "." in text:
            tokens = text.split(".")
            text = tokens[0] + "." + tokens[1][:2] # keep 2 decimal places
        return text

    @staticmethod
    def resize_image(srcpath, dstpath, size, text=None):
        cmd = ["convert", srcpath, "-resize",
               "{}x{}".format(size, size)]
        if text:
            cmd += ["-font", "helvetica",
                    "-fill", "gray",
                    "-pointsize", "20",
                    "-gravity", "South",
                    "-draw", "text 12,8 '%s'" % text]
            cmd += ["-font", "helvetica",
                    "-fill", "white",
                    "-pointsize", "20",
                    "-gravity", "South",
                    "-draw", "text 10,10 '%s'" % text]
#            cmd += ["-gravity", "Center", "-pointsize", "12", "-annotate", "0", text]
        cmd += [dstpath]
        result = run(cmd)
        if result is None:
            return None
        return dstpath

    @staticmethod
    def thumbnail(path, fname, size=240):
        """Returns thumbnail path"""
        mime_type = Store.mime_type(path)
        thumbnail_path = os.path.join(Config.thumbnail_dir, fname)
        if not thumbnail_path.endswith(".png"):
            thumbnail_path += ".png"

        # try creating a thumbnail
        if "image" in mime_type:
            return Store.resize_image(path, thumbnail_path, size)

        elif "video" in mime_type:
            tmpframe = Store.video_frame(path)
            duration = Store.video_duration(path)
            return Store.resize_image(tmpframe, thumbnail_path, size, text=duration)

        return None

    # -------------------------------------------
    # Commit API

    @contextmanager
    def batch(self):
        """
        If batch is invoked, batch modification events are happening and
        thus a commit is deferred until all batch are exitted

        with store.batch():
            # call process one or more times

        On exit of the batch context, commit happens automatically

        store.batch() can be recursing. Exit from the outermost context
        causes a commit.
        """
        before_ctx_count = self.commit_ctx_depth
        self.commit_ctx_depth += 1
        trace("commit_ctx_depth", self.commit_ctx_depth)

        yield

        assert self.commit_ctx_depth == before_ctx_count + 1
        self.commit_ctx_depth -= 1

        if self.commit_ctx_depth == 0:
            self.commit()

    def commit(self):
        if self.commit_ctx_depth == 0:
            trace("commit")
            self.conn.commit()
        else:
            trace("skipping commit. commit_ctx_depth", self.commit_ctx_depth)

    # -------------------------------------------
    # Modifying DB

    def _add(self, path, fname, exif):
        trace(fname, "found new file")
        ts = now()
        thumbnail_path = Store.thumbnail(path, fname)
        self.metadata.insert(
                fname=fname,
                hash_sha256=hash_sha256(path),
                time_db_added=ts,
                time_db_updated=ts,
                deleted=False,
                desc="",
                exif=exif,
                mime_type=exif['MIMEType'],
                exif_img_create_date=exif.get('CreateDate', exif.get("FileModifyDate")),
                thumbnail=thumbnail_path)
        self.commit()

    def _delete(self, path, fname, existing_data):
        assert existing_data
        deleted_idx = Metadata.column_idx("deleted")
        if existing_data[deleted_idx]:
            # nothing to do
            return

        trace(fname, "deleted")
        self.metadata.update(
                {"deleted": True},
                {"fname": fname})
        self.commit()

    def _update(self, path, fname, exif, existing_data):
        trace(fname, "updating existing data")
        ts = now()
        thumbnail_path = Store.thumbnail(path, fname)
        self.metadata.update(
                {"hash_sha256": hash_sha256(path),
                 "time_db_updated": ts,
                 "deleted": False,
                 "exif": exif,
                 "mime_type": exif['MIMEType'],
                 "exif_img_create_date": exif.get("CreateDate", exif.get("FileModifyDate")),
                 "thumbnail_path": thumbnail_path},
                {"fname": fname})
        self.commit()

    def process(self, path):
        fname = os.path.split(path)[1]

        exif = None

        try:
            exif = exif_api.get_info(path)
        except Exception as exc:
            trace("ExifApi failed for", path, "Error:", exc)
            pass

        ts = now()
        existing_data = self.metadata.get('*',
                                          where={"fname": fname})
        existing_data = existing_data[0] if existing_data else None

        if not existing_data and exif:
            self._add(path, fname, exif)

        elif existing_data and not exif:
            self._delete(path, fname, existing_data)

        elif not exif or Store.samefile(path, fname, exif, existing_data):
            # nothing to do
            return

        else:
            self._update(path, fname, exif, existing_data)

    # -------------------------------------------
    # Fetching metadata

    def get_db_data(self, deleted=None, reverse=False):
        where = {}
        if deleted is not None:
            where["deleted"] = deleted
        data = self.metadata.get('*', where=where,
                                 order_by=["exif_img_create_date " +
                                           ("asc" if reverse else "desc")])
        return data

    def get_db_data_fname(self, fname):
        data = self.metadata.get('*', {"fname": fname})
        if data:
            return data[0]
        return None

def update_metadata(files):
    with store.batch():
        for path in files:
            store.process(path)

if __name__ == "__main__":
    import sys
    store = Store()
    #store.get_db_data()
    #update_metadata(sys.argv[1:])
    print(Store.upload_dir_disk_usage())
