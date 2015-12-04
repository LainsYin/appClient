# appClient


"""   配置文件格式说明
更具功能号配置每个section
每个section包括两个键 分别header和body
header ＝ 17, 100, 90001, 65536, 0 , 520
第三位是功能号，第五位是长度设置为0。其他每位的解释查看相关协议文档
body ＝ { "message": "hello world", "type": 1, "touid": "60HNr67d"}
body是json或是xml格式

app  连信息服务器端口3050
box  连信息服务器端口58849
box  初始化端口11235
"""

执行说明
************************************************************
$ ./client.py -h
Usage: client.py [options]

Options:
  -h, --help            show this help message and exit
  -i HOST, --host=HOST  specify host, default is 192.168.1.156
  -p PORT, --port=PORT  specify port, default is 3050
  -f FUN, --fun=FUN     specify function num, default is 90001
  -n NUM, --num=NUM     specify threads num, default is 1
  -d, --daemon          set daemon process, default is true

详细信息查看client.log
json格式例子
$ ./client.py -f 90003
INFO     start 1 threads to server 192.168.1.156:3050 ...
INFO     new connection 1 to 192.168.1.156:3050
INFO     Waiting for 1 second
INFO     received data :  17, 100, 90003, 65536, 113, 520
INFO     received data :  {u'status': 0, u'server': u'http://192.168.1.199', u'id': 1, u'infoserver': u'http://192.168.1.199'}

$ ./client.py -p 11235 -f 10001
INFO     start 1 threads to server 192.168.1.156:11235 ...
INFO     new connection 1 to 192.168.1.156:11235
INFO     Waiting for 1 second
INFO     received data :  header:17, 100, 10001, 65536, 49, 4294967295
INFO     received data :  body:<root><status>0</status><result>2</result></root>

