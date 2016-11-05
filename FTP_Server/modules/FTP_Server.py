# /usr/bin/env python
# coding:utf-8
# author:ZhaoHu

import socketserver
import os
import re
import sys
import json
import subprocess
# import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from lib import commons

ip_port = ('0.0.0.0', 10086)

CURRENT_USER_INFO = {}


class MyServer(socketserver.BaseRequestHandler):

    # def view_bar(self, current_size, total_size):
    #     rate = current_size / total_size
    #     rate_num = int(rate * 100)
    #     print('file transporting... | %-25s | \033[31;1m%3d%%\033[0m' % ('>' * (rate_num // 4), rate_num), end='\r')
    #     time.sleep(0.01)

    def login(self, user_dict):
        """
        user login verify
        :param user_dict: user info dict
        :return:
        """
        all_user_dict = json.load(open(settings.USER_INFO_DIR, 'r'))
        for item in enumerate(all_user_dict):
            if user_dict['username'] == all_user_dict.get(item[1]).get('username'):
                if commons.md5(user_dict['password']) == all_user_dict.get(item[1]).get('password'):
                    CURRENT_USER_INFO['disk_quota'] = all_user_dict.get(item[1]).get('disk_quota')
                    return True

    def file_recv(self, file_name, file_md5, file_size, current_size, d_value, write_method):
        """
        receive file
        :param file_name: file name
        :param file_size: file size
        :param current_size: current file szie
        :param write_method: the method of write file
        :return:
        """
        notify_info = {'current_size': current_size, 'stat': 'ok', 'chazhi': d_value}
        self.request.sendall(bytes(json.dumps(notify_info), encoding='utf-8'))  # ask client to start transport file
        with open(file_name, write_method) as new_file:
            recv_size = current_size
            while recv_size < file_size:
                data = self.request.recv(4096)
                recv_size += len(data)
                new_file.write(data)
                # self.view_bar(recv_size, file_size)
            print('%s receive successful' % file_name)
        local_md5 = commons.get_file_md5(file_name)
        print('本地 %s | 客户端 %s' % (local_md5, file_md5))
        if local_md5 == file_md5:
            msg = '\033[31;1mThe file in server and the local file are just the same\033[0m'
            self.request.sendall(bytes(msg, encoding='utf-8'))
            print(msg)
        else:
            msg = '\033[31;1mThe file in server and the local file are different\033[0m'
            self.request.sendall(bytes(msg, encoding='utf-8'))
            print(msg)

    def task_put(self, file_info):
        """
        upload file
        :param file_info: about file info
        :return:
        """
        file_name = os.path.join(CURRENT_USER_INFO.get('home_dir'), file_info.get('filename'))
        file_size = file_info.get('filesize')
        file_md5 = file_info.get('filemd5')
        print(file_name, file_size, file_md5)
        user_disk_quota = int(CURRENT_USER_INFO.get('disk_quota'))
        user_current_dir = CURRENT_USER_INFO.get('current_dir')
        used_quota_size_cmd = 'cd ' + user_current_dir + '&&' + 'du -sb'
        used_quota_size = subprocess.Popen(used_quota_size_cmd, shell=True, stdout=subprocess.PIPE)
        used_quota_size = used_quota_size.stdout.read().decode()
        used_quota_size = re.split(r'(\d+)', used_quota_size)[1]  # get used disk size and to int
        total_sum = int(used_quota_size) + int(file_size)
        d_value = total_sum - user_disk_quota  # the rest of disk quota
        if total_sum > user_disk_quota:
            notify_info = {'stat': 'large', 'chazhi': d_value}
            self.request.sendall(bytes(json.dumps(notify_info), encoding='utf-8'))
        elif not os.path.exists(file_name):  # local file not exist, 'w' mode to write
            self.file_recv(file_name, file_md5, file_size, 0, d_value, 'wb')
        else:
            current_file_size = os.stat(file_name).st_size
            print('file exist~, current_size:', current_file_size)
            if current_file_size < file_size:  # local file exist but not complete, 'a' mode to write
                self.file_recv(file_name, file_md5, file_size, current_file_size, d_value, 'ab')
            else:  # file complete, only notify client
                notify_info = {'current_size': current_file_size, 'stat': 'no'}
                self.request.sendall(bytes(json.dumps(notify_info), encoding='utf-8'))

    def task_get(self, file_info):
        """
        download file
        :param file_info: about file info
        :return:
        """
        abs_file_path = file_info.get('filename')  # server file abs path
        if not abs_file_path.startswith(CURRENT_USER_INFO.get('home_dir')):  # file must in current user home dir
            exist_or_not = {'priority': 'no'}
            self.request.sendall(bytes(json.dumps(exist_or_not), encoding='utf-8'))
        else:
            if not os.path.exists(abs_file_path):  # file not exist
                exist_or_not = {'exist': 'no'}
                self.request.sendall(bytes(json.dumps(exist_or_not), encoding='utf-8'))
            else:
                file_size = os.stat(abs_file_path).st_size
                file_name = abs_file_path.split(os.sep)[-1]
                file_md5 = commons.get_file_md5(abs_file_path)
                print(file_name, file_size, file_md5)
                exist_or_not = {'exist': 'yes', 'filename': file_name, 'filesize': file_size, 'filemd5': file_md5}
                self.request.sendall(bytes(json.dumps(exist_or_not), encoding='utf-8'))  # send file info to client
                notify_info = json.loads(self.request.recv(1024).decode())  # receive client notify info
                if notify_info.get('stat') == 'ok':
                    with open(abs_file_path, 'rb') as file:
                        file.seek(notify_info.get('current_size'))
                        for line in file:
                            self.request.sendall(line)
                    print('\033[31;1mMission complate .. \033[0m')
                    send_success_msg = self.request.recv(1024).decode()
                    print(send_success_msg)
                else:
                    print('\033[31;1mclient file already exists\033[0m')

    def task_mission(self, cmd):
        """
        for some cmd which need to judge user_home_dir
        :param cmd:
        :return:
        """
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        result = result.stdout.read()
        if not result:
            result_info = json.dumps({'tag': 'null'})
            self.request.sendall(bytes(result_info, encoding='utf-8'))
        else:
            result_info = json.dumps({'result_len': len(result)})
            self.request.sendall(bytes(result_info, encoding='utf-8'))
            start_tag = self.request.recv(1024).decode()
            if start_tag.startswith('start'):
                self.request.sendall(result)
            print('send all successfully')

    def ls_or_dir(self, file_info):
        """
        for ls and dir
        :param file_info:
        :return:
        """
        cmd = file_info.get('cmd')
        user_current_dir = CURRENT_USER_INFO.get('current_dir')
        full_cmd = 'cd ' + user_current_dir + '&&' + cmd  # join full cmd
        self.task_mission(full_cmd)

    def task_ls(self, file_info):
        """
        cmd ls
        :param file_info:
        :return:
        """
        self.ls_or_dir(file_info)

    def task_dir(self, file_info):
        """
        cmd dir
        :param file_info:
        :return:
        """
        self.ls_or_dir(file_info)

    def task_du(self, file_info):
        """
        cmd du
        :param file_info:
        :return:
        """
        self.ls_or_dir(file_info)

    def task_df(self, file_info):
        """
        cmd df
        :param file_info:
        :return:
        """
        cmd = file_info.get('cmd')
        self.task_mission(cmd)

    def task_uname(self, file_info):
        """
        cmd uname
        :param file_info:
        :return:
        """
        cmd = file_info.get('cmd')
        self.task_mission(cmd)

    def task_ifconfig(self, file_info):
        """
        cmd ifconfig
        :param file_info:
        :return:
        """
        cmd = file_info.get('cmd')
        self.task_mission(cmd)

    def send_dir_data(self, dir_name):
        """
        for task_cd use this func
        :param dir_name:
        :return:
        """
        result_info = json.dumps({'result_len': len(dir_name)})
        self.request.sendall(bytes(result_info, encoding='utf-8'))
        start_tag = self.request.recv(1024).decode()
        if start_tag.startswith('start'):
            self.request.sendall(bytes(dir_name, encoding='utf-8'))
        print('send all successfully')

    def task_pwd(self, file_info):
        """
        cmd pwd
        :param file_info:
        :return:
        """
        self.send_dir_data(CURRENT_USER_INFO.get('current_dir'))

    def task_cd(self, file_info):
        cmd = file_info.get('cmd')
        cmd_list = cmd.split()
        user_home_dir = CURRENT_USER_INFO.get('home_dir')
        if len(cmd_list) == 1:  # only cd
            CURRENT_USER_INFO['current_dir'] = user_home_dir
            self.send_dir_data(user_home_dir)
        else:
            cmd2 = cmd_list[1]
            if cmd2 == '~':  # cd ~
                CURRENT_USER_INFO['current_dir'] = user_home_dir
                self.send_dir_data(user_home_dir)
            elif cmd2.startswith('~/'):  # cd ~/[.*]
                the_other_dir = cmd2.split('~/')[-1]
                if not os.path.exists(os.path.join(user_home_dir, the_other_dir)):
                    result_info = json.dumps({'tag': 'not_exists'})
                    self.request.sendall(bytes(result_info, encoding='utf-8'))
                else:
                    if the_other_dir:
                        CURRENT_USER_INFO['current_dir'] = os.path.join(user_home_dir, the_other_dir)
                        self.send_dir_data(CURRENT_USER_INFO.get('current_dir'))
                    else:
                        self.send_dir_data(CURRENT_USER_INFO.get('current_dir'))
            elif cmd_list[1] == '..' or cmd_list[1] == '../':  # cd .. or cd ../
                user_current_dir = CURRENT_USER_INFO.get('current_dir')
                user_upper_dir = os.path.dirname(user_current_dir)
                if user_upper_dir.startswith(user_home_dir):
                    CURRENT_USER_INFO['current_dir'] = user_upper_dir
                    self.send_dir_data(user_upper_dir)
                else:
                    result_info = json.dumps({'tag': 'no_priority'})
                    self.request.sendall(bytes(result_info, encoding='utf-8'))
            elif cmd_list[1] == '../..' or cmd_list[1] == '../../':  # cd ../.. or cd ../../
                user_current_dir = CURRENT_USER_INFO.get('current_dir')
                user_upper2_dir = os.path.dirname(os.path.dirname(user_current_dir))
                if user_upper2_dir.startswith(user_home_dir):
                    CURRENT_USER_INFO['current_dir'] = user_upper2_dir
                    self.send_dir_data(user_upper2_dir)
                else:
                    result_info = json.dumps({'tag': 'no_priority'})
                    self.request.sendall(bytes(result_info, encoding='utf-8'))
            else:  # cd [.*]
                if not cmd2.startswith('/'):  # eg. cd abc
                    if not os.path.exists(os.path.join(CURRENT_USER_INFO.get('current_dir'), cmd2)):
                        result_info = json.dumps({'tag': 'not_exists'})
                        self.request.sendall(bytes(result_info, encoding='utf-8'))
                    else:  # relative path
                        CURRENT_USER_INFO['current_dir'] = os.path.join(CURRENT_USER_INFO.get('current_dir'), cmd2)
                        self.send_dir_data(CURRENT_USER_INFO['current_dir'])
                elif not cmd2.startswith(user_home_dir):  # eg. cd /abc/def...
                    result_info = json.dumps({'tag': 'no_priority'})
                    self.request.sendall(bytes(result_info, encoding='utf-8'))
                else:  # eg. cd ~/abc  --> '~' point to user home dir
                    if not os.path.exists(cmd2):
                        result_info = json.dumps({'tag': 'not_exists'})
                        self.request.sendall(bytes(result_info, encoding='utf-8'))
                    else:
                        CURRENT_USER_INFO['current_dir'] = cmd2
                        self.send_dir_data(cmd2)

    def handle(self):
        """
        handle method, first to run
        :return:
        """
        self.request.sendall(bytes('Welcome to here~', encoding='utf-8'))
        while True:  # user login
            user_info = self.request.recv(1024).decode()
            CURRENT_USER_INFO['username'], CURRENT_USER_INFO['password'] = user_info.split(':')
            login_or_not = self.login(CURRENT_USER_INFO)
            if login_or_not:
                print('login successful')
                CURRENT_USER_INFO['home_dir'] = os.path.join(settings.USER_HOME_DIR, CURRENT_USER_INFO['username'])
                CURRENT_USER_INFO['current_dir'] = CURRENT_USER_INFO.get('home_dir')
                self.request.sendall(bytes('True', encoding='utf-8'))
                break
            else:
                print('login failed')
                self.request.sendall(bytes('False', encoding='utf-8'))
                continue
        while True:  # user choice to run
            print('current_dir:%s ;home_dir:%s ;disk_quota:%s' %
                  (CURRENT_USER_INFO.get('current_dir'), CURRENT_USER_INFO.get('home_dir'),
                   CURRENT_USER_INFO.get('disk_quota')))
            task_data = self.request.recv(1024).decode()
            task_data = json.loads(task_data)
            if hasattr(self, 'task_%s' % task_data.get('action')):
                user_action = getattr(self, 'task_%s' % task_data.get('action'))
                user_action(task_data)
                continue
            else:
                result_info = json.dumps({'tag': 'failed'})
                self.request.sendall(bytes(result_info, encoding='utf-8'))

if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(ip_port, MyServer)
    server.serve_forever()
