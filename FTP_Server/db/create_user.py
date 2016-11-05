# /usr/bin/env python
# coding:utf-8
# author:ZhaoHu

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commons

user_info = {
    '1': {'username': 'zhaohu', 'password': commons.md5('123'), 'disk_quota': '100000000'},
    '2': {'username': 'test', 'password': commons.md5('123'), 'disk_quota': '10000000'}
}

json.dump(user_info, open('user_info', 'w'))

for key in enumerate(user_info):
    os.mkdir(user_info.get(key[1]).get('username'))
