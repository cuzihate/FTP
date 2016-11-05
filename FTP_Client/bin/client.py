# /usr/bin/env python
# coding:utf-8
# author:ZhaoHu

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import FTP_Client as client

if __name__ == '__main__':
    client.main()