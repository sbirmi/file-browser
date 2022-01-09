#!/usr/bin/env python3
from collections import defaultdict
from Metadata import Store

store = Store()

all_data = store.get_db_data()

grouped_data = defaultdict(list)

for row in all_data:
    key = (row.exif['FileSize'],
           row.hash_sha256)
    grouped_data[key].append(row)

for key, matches in grouped_data.items():
    if len(matches) == 1:
        continue

    print("")
    print("-----------------------")

    for match in matches:
        print(match.fname)

