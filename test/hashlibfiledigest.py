"""Hashing file using hashlib.file_digest function added in version 3.11."""

import hashlib

with open(__file__, "rb") as fptr:
    digest = hashlib.file_digest(fptr, hashlib.sha1).hexdigest()
    print(f"Sha1 sum of {__file__} is {digest}")
