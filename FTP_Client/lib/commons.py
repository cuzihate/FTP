# /usr/bin/env python
# coding:utf-8
# author:ZhaoHu

import hashlib
import os


def md5(arg):  # simple str md5
    """
    str md5
    :param arg:
    :return:
    """
    obj = hashlib.md5(bytes('wtf', encoding='utf-8'))
    obj.update(bytes(arg, encoding='utf-8'))
    return obj.hexdigest()


def get_file_md5(filename):  # for file
    """
    file md5
    :param filename:
    :return:
    """
    if not os.path.isfile(filename):
        return
    obj = hashlib.md5()
    with open(filename, 'rb') as file:
        while True:
            content = file.read(8096)
            if not content:
                break
            obj.update(content)
    return obj.hexdigest()
