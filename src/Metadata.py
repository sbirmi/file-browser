from contextlib import contextmanager
import json
import os
import sqlite3
import subprocess

from HashLib import hash_sha256

from Config import thumbnail_dir
from Storage import (
        Bool,
        Int,
        Json,
        Table,
        Timestamp,
        Txt,
)
from Utils import (
        now,
        trace,
)


METADATA_FILE = "00_metadata.sqlite3"

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
    def __init__(self, fname=METADATA_FILE):
        self.fname = fname
        self.conn = sqlite3.connect(self.fname)
        self.cursor = self.conn.cursor()
        self.metadata = Metadata(self.cursor)

        self.commit_ctx_depth = 0
        self.commit()

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
    def thumbnail(path, fname, size=240):
        thumbnail_path = os.path.join(thumbnail_dir, fname)
        # try creating a thumbnail
        try:
            cmd = ["convert", path, "-resize", str(size), thumbnail_path]
            subprocess.call(cmd)
        except Exception as exc:
            return None

        return thumbnail_path

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

    def get_db_data(self):
        data = self.metadata.get('*')
        return data

def update_metadata(files):
    with store.batch():
        for path in files:
            store.process(path)

if __name__ == "__main__":
    import sys
    store = Store()
    #store.get_db_data()
    update_metadata(sys.argv[1:])
