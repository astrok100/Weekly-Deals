"""File system related facilities.
"""

import os
import gzip


def list_dir(dir_path):
    dir_exists(dir_path)
    return os.listdir(dir_path)


def dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def write_file(fname, html_body):
    dir_path = os.path.dirname(fname)
    dir_exists(dir_path)

    with open(fname, 'w') as html_file:
        html_file.write(html_body)


def write_gzip(fname, html_body):
    dir_path = os.path.dirname(fname)
    dir_exists(dir_path)

    with gzip.open(fname, 'wb') as html_file:
        html_file.write(html_body)
