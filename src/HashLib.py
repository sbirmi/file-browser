import hashlib

def hash_sha256(path):
    h = hashlib.sha256()

    with open(path, 'rb') as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()
