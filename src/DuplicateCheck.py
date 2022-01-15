#!/usr/bin/env python3
from collections import defaultdict
import os
import subprocess
import sys

import Config
from Metadata import Store

store = Store()

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
                os.remove(upload_path(match.fname))
                os.remove(thumbnail_path(match.fname))
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


if __name__ == "__main__":
    all_data = store.get_db_data(skip_deleted=True)

    grouped_data = defaultdict(list)

    for row in all_data:
        key = (row.exif['FileSize'],
               row.hash_sha256)
        grouped_data[key].append(row)

    for key, matches in grouped_data.items():
        if len(matches) == 1:
            continue
        
        process_possible_duplicates(matches)
