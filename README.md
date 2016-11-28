

 - FTP 客户端与服务端分离，服务端在ubuntu的Pycharm上执行通过

 - FTP 服务端有俩用户，分别为 zhaohu 和 test ，密码为 123 ， 磁盘配额分别为 100M 和 10M（文件中以字节表示）,
   服务端可自定义用户信息，文件路径在 FTP_Server/db/create_user.py

 - 用户均有自己的家目录，为测试方便，用户zhaohu家目录下有 1 和 2 及其子文件夹

 - 服务端支持的命令有：
	ls/dir/du/df/uname/pwd/ifconfig/cd

 - 作业中的要求均基本支持
