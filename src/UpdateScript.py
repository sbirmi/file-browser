#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sqlite3
import subprocess
import sys

import Config
import Metadata as MetadataModule
from Storage import (
        Bool,
        Int,
        Json,
        Table,
        Timestamp,
        Txt,
)

store = MetadataModule.Store()

def delete_path(path):
    try:
        os.remove(path)
    except:
        print("Failed to deleted", path)
        pass

def upload_path(fname):
    return os.path.join(Config.upload_dir, fname)

def thumbnail_path(fname):
    return os.path.join(Config.thumbnail_dir, fname)

def ask(msg, options):
    inp = None
    while inp not in options:
        inp = input(msg)

    return inp

def same_file(fname1, fname2):
    path1 = upload_path(fname1)
    path2 = upload_path(fname2)
    assert(os.path.exists(path1))
    assert(os.path.exists(path2))

    cmd = ["diff", path1, path2]
    try:
        subprocess.check_output(cmd)
    except:
        return False
    return True

def process_possible_duplicates(matches):
    print("")
    print("-----------------------")

    for match in matches:
        print(match.fname)

    print()

    if all(same_file(matches[0].fname, other.fname) for other in matches[1:]):
        choice = ask("Duplicates detected. (d)elete all but first   (k)eep all  (q)uit? ", {"d", "k", "q"})
        if choice == "q":
            print("Quitting")
            sys.exit(0)
        if choice == "k":
            print("Skipping")
            return

        for match in matches[1:]:
            try:
                delete_path(upload_path(match.fname))
                delete_path(thumbnail_path(match.fname))
                print("Deleted successfully")
            except:
                print("Failed to delete uploaded file or thumbnail")

            store._delete(upload_path(match.fname), match.fname, match)

    else:
        print("Files are not duplicates. Not sure what to do")
        choice = ask("(k)eep all  (q)uit? ", {"k", "q"})
        if choice == "q":
            print("Quitting")
            sys.exit(0)
        if choice == "k":
            print("Skipping")
            return

# -----------------------------------------------
# Update actions

def duplicate_check():
    all_data = store.get_db_data(deleted=False, reverse=True)

    grouped_data = defaultdict(list)

    for row in all_data:
        key = (row.exif['FileSize'],
               row.hash_sha256)
        grouped_data[key].append(row)

    for key, matches in grouped_data.items():
        if len(matches) == 1:
            continue
        
        process_possible_duplicates(matches)

def update_thumbnails(fnames):
    def get_data(fnames):
        if fnames:
            for fname in fnames:
                yield store.get_db_data_fname(fname)
        else:
            all_data = store.get_db_data(deleted=False)
            for item in all_data:
                yield item

    with store.batch():
        for entry in get_data(fnames):
            old_thumbnail_path = entry.thumbnail
            thumbnail_path = MetadataModule.Store.thumbnail(Config.upload_path(entry.fname), entry.fname)
            if old_thumbnail_path != thumbnail_path and old_thumbnail_path:
                delete_path(old_thumbnail_path)
            store.metadata.update({"thumbnail": thumbnail_path}, {"fname": entry.fname})

# -----------------------------------
# Map data to this new Metadata
# format
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

def translate_row(old_row):
    """Translate a row of data from the old format
    MetadataModule.Metadata to Metadata table defined
    in this file"""
    if not old_row[-1]: # No thumbnail
        return old_row
    try:
        new_row = tuple(list(old_row[:-1]) + [os.path.split(old_row[-1])[-1]])
    except Exception as exc:
        import pdb; pdb.set_trace()
        pass
    return new_row

def map_data(new_file):
    assert not os.path.exists(new_file), "New file must not exist"

    old_file = Config.metadata_file
    old_conn = sqlite3.connect(old_file)
    old_cursor = old_conn.cursor()
    old_table = MetadataModule.Metadata(old_cursor)
    old_data = old_table.get('*')
    old_cursor.close()
    old_conn.close()

    new_conn = sqlite3.connect(new_file)
    new_cursor = new_conn.cursor()
    new_table = Metadata(new_cursor)

    new_columns = new_table.columns()
    for idx, old_row in enumerate(old_data):
        new_row = translate_row(old_row)
        new_table.insert(**dict(zip(new_columns, new_row)))

    new_conn.commit()
    print("Copied {} rows".format(idx))

def main(args):
    if args.map_data:
        assert not args.paths, "Can't specify upload file paths with --map-data"
        map_data(args.map_data)
        return

    if args.duplicate_check:
        assert not args.paths
        duplicate_check()
        return

    if args.update_thumbnails:
        fnames = [os.path.split(path)[1] for path in args.paths]
        update_thumbnails(fnames)
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--duplicate-check",
                        action="store_true")
    parser.add_argument("-t", "--update-thumbnails",
                        action="store_true")
    parser.add_argument("--map-data", metavar="NEW_SQLITE3_FILE")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    main(args)
