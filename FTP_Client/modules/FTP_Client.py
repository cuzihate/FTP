# /usr/bin/env python
# coding:utf-8
# author:ZhaoHu

import socket
import json
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commons

ip_port = ('172.16.111.130', 10086)
socket_obj = socket.socket()

def view_bar(current_size, total_size):
    """
    进度条
    :param current_size:
    :param total_size:
    :return:
    """
    rate = current_size / total_size
    rate_num = int(rate * 100)
    print('file transporting ... | %-25s | \033[31;1m%3d%%\033[0m' % ('>' * (rate_num // 4), rate_num), end='\r')
    time.sleep(0.01)

def login(username, password):
    """
    登录
    :param username:
    :param password:
    :return:
    """
    socket_obj.sendall(bytes(username + ':' + password, encoding='utf-8'))
    ret = socket_obj.recv(1024).decode()
    if ret == 'True':
        return True

def put():
    """
    上传文件
    :return:
    """
    while True:
        user_input = input('put xxx : ').strip()
        if user_input == 'q':
            break
        cmd_list = user_input.split()
        # print(cmd_list)
        if len(cmd_list) < 2:
            print('\033[31;1m命令不合法\033[0m')
            continue
        if cmd_list[0] == 'put':
            if os.path.exists(cmd_list[1]):  # 本地文件存在
                file_name = cmd_list[1].split(os.sep)[-1]
                file_size = os.stat(cmd_list[1]).st_size
                file_md5 = commons.get_file_md5(cmd_list[1])
                print('file:%s, size: %s, md5: %s' % (file_name, file_size, file_md5))
                file_info = {'action': 'put', 'filename': file_name, 'filesize': file_size, 'filemd5': file_md5}
                socket_obj.sendall(bytes(json.dumps(file_info), encoding='utf-8'))  # 将文件相关信息发送给服务器
                notify_info = json.loads(socket_obj.recv(1024).decode())  # 接收服务器的通知消息
                current_size = notify_info.get('current_size')  # 服务端已存在文件大小，不存在为0 --》断点续传
                if notify_info.get('stat') == 'ok':
                    with open(cmd_list[1], 'rb') as file:
                        file.seek(current_size)  # 断点续传
                        for line in file:
                            socket_obj.sendall(line)
                            current_size += len(line)
                            view_bar(current_size, file_size)  # 调用进度条
                    the_rest_size = notify_info.get('chazhi')
                    print('\033[31;1mMission complate ..磁盘剩余空间 %s 字节 \033[0m' % (-the_rest_size))
                    send_success_msg = socket_obj.recv(1024).decode()
                    print(send_success_msg)
                    break
                elif notify_info.get('stat') == 'large':
                    chazhi = notify_info.get('chazhi')
                    print('\033[31;1m文件 %s 太大了。。磁盘空间不足, 多了 %s 字节\033[0m' % (cmd_list[1], chazhi))
                else:
                    print('file exists')
                    break
            else:
                print('\033[31;1m文件 %s 不存在\033[0m' % cmd_list[1])
                continue
        else:
            print('\033[31;1m命令不合法\033[0m')
            continue

def file_recv(file_name, file_md5, file_size, current_size, write_method):
    """
    下载文件传输
    :param file_name: 文件名
    :param file_size: 文件大小
    :param current_size: 已存在文件大小
    :param write_method: 读写方式 wb or ab
    :return:
    """
    notify_info = {'current_size': current_size, 'stat': 'ok'}
    socket_obj.sendall(bytes(json.dumps(notify_info), encoding='utf-8'))  # ask server to start transport file
    with open(file_name, write_method) as new_file:  # 接收写文件
        recv_size = current_size
        while recv_size < file_size:
            data = socket_obj.recv(4096)
            recv_size += len(data)
            new_file.write(data)
            view_bar(recv_size, file_size)
        print('%s receive successful' % file_name)
    local_file_md5 = commons.get_file_md5(file_name)
    print('本地 %s | 服务器 %s' % (local_file_md5, file_md5))
    if local_file_md5 == file_md5:
        msg = '\033[31;1mThe file in server and the local file are just the same\033[0m'
        socket_obj.sendall(bytes(msg, encoding='utf-8'))
        print(msg)
    else:
        msg = '\033[31;1mThe file in server and the local file are different\033[0m'
        socket_obj.sendall(bytes(msg, encoding='utf-8'))
        print(msg)
def get():
    """
    下载文件
    :return:
    """
    while True:
        user_input = input('get xxx : ').strip()
        if user_input == 'q':
            break
        cmd_list = user_input.split()
        if len(cmd_list) != 2:
            print('\033[31;1m命令不合法\033[0m')
            continue
        if cmd_list[0] == 'get':
            file_info = {'action': 'get', 'filename': cmd_list[1]}
            socket_obj.sendall(bytes(json.dumps(file_info), encoding='utf-8'))  # 通知服务器调用get方法
            exist_or_not = json.loads(socket_obj.recv(1024).decode())  # 接收服务端通知
            if exist_or_not.get('exist') == 'no':  # 服务端文件不存在
                print('\033[31;1mFTP server file not exist!\033[0m')
                continue
            elif exist_or_not.get('priority') == 'no':  # 服务端文件存在，但是用户无权下载
                print('\033[31;1m没有权限。。\033[0m')
                continue
            else:
                file_name = exist_or_not.get('filename')
                file_size = exist_or_not.get('filesize')
                file_md5 = exist_or_not.get('filemd5')
                print('文件 %s 大小为 %s md5 %s' % (cmd_list[1], file_size, file_md5))
                if not os.path.exists(file_name):  # 服务端文件存在，本地不存在
                    file_recv(file_name, file_md5, file_size, 0, 'wb')  # 直接 w 写
                    break
                else:
                    exist_file_size = os.stat(file_name).st_size  # 本地存在文件大小
                    if exist_file_size < file_size:
                        print('\033[31;1mfile %s exist, but incomplete! size: %s\033[0m' % (file_name, exist_file_size))
                        file_recv(file_name, file_md5, file_size, exist_file_size, 'ab')  # 断点续传，a 追加模式
                        break
                    else:
                        notify_info = {'stat': 'no'}  # 本地文件完整，通知服务端无需操作
                        socket_obj.sendall(bytes(json.dumps(notify_info), encoding='utf-8'))
                        print('\033[31;1mfile %s already exist now, size: %s\033[0m' % (file_name, exist_file_size))
                        break
        else:
            print('\033[31;1m命令不合法\033[0m')
            continue

def run_cmd():
    """
    执行命令
    :return:
    """
    while True:
        user_input = input('长度为2的简单命令: ').strip()
        if user_input == 'q':
            break
        cmd_list = user_input.split()
        if not cmd_list or len(cmd_list) > 2:
            print('\033[31;1m命令不合法\033[0m')
            continue
        else:  # 只有长度为2的命令才会发送给服务端
            cmd_info = {'action': cmd_list[0], 'cmd': user_input}
            socket_obj.sendall(bytes(json.dumps(cmd_info), encoding='utf-8'))
            result_info = json.loads(socket_obj.recv(1024).decode())  # 接收服务端回复
            if result_info.get('tag') == 'not_exists':  # 不同标志位代表不同意思
                print('\033[31;1m系统路径不存在\033[0m')
                continue
            elif result_info.get('tag') == 'no_priority':
                print('\033[31;1m没有权限\033[0m')
                continue
            elif result_info.get('tag') == 'null':
                print('\033[31;1m没有内容，返回值为空~\033[0m')
                continue
            elif result_info.get('tag') == 'failed':
                print('\033[31;1m输入命令有误或不支持，请重新输入\033[0m')
                continue
            else:
                result_len = result_info.get('result_len')
                socket_obj.sendall(bytes('start to trans..', encoding='utf-8'))  # 通知服务端发送数据
                recv_size = 0
                recv_msg = b''
                while recv_size < result_len:  # 循环接收数据，防止黏包
                    recv_data = socket_obj.recv(1024)
                    recv_msg += recv_data
                    recv_size += len(recv_data)
                    # print('MSG SIZE %s RECV SIZE %s' % (result_len, recv_size))
                print(recv_msg.decode())



menu_dict = {
    '1': put,
    '2': get,
    '3': run_cmd
}

def main():
    socket_obj.connect(ip_port)
    welcome_msg = socket_obj.recv(1024).decode()
    print(welcome_msg)
    while True:
        username = input('用户名：').strip()
        password = input('密  码：').strip()
        if username and password:
            login_or_not = login(username, password)
            if login_or_not:  # login successful
                print('登录成功~')
                break
            else:
                print('用户名或密码错误，请重新输入')
        else:
            print('用户名或密码不能为空，请重新输入')
    while True:
        user_choice = input('1、上传 | 2、下载 | 3、执行命令 | 其余选项退出: ').strip()
        if user_choice in menu_dict:
            menu_dict[user_choice]()
        else:
            print('bye~')
            break


if __name__ == '__main__':
    main()
