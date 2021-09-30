# encoding:utf-8
import socket
import _thread
import socks 

 
class Header:
    """
    用于读取和解析头信息 commit test
    """
 
    def __init__(self, conn):
        self._method = None
        header = b''
        try:
            while 1:
                data = conn.recv(4096)
                header = b"%s%s" % (header, data)
                if header.endswith(b'\r\n\r\n') or (not data):
                    break
        except:
            pass
        self._header = header
        self.header_list = header.split(b'\r\n')
        self._host = None
        self._port = None
 
    def get_method(self):
        """
        获取请求方式
        :return:
        """
        if self._method is None:
            self._method = self._header[:self._header.index(b' ')]
        return self._method
 
    def get_host_info(self):
        """
        获取目标主机的ip和端口
        :return:
        """
        if self._host is None:
            method = self.get_method()
            line = self.header_list[0].decode('utf8')
            if method == b"CONNECT":
                host = line.split(' ')[1]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 443
            else:
                for i in self.header_list:
                    if i.startswith(b"Host:"):
                        host = i.split(b" ")
                        if len(host) < 2:
                            continue
                        host = host[1].decode('utf8')
                        break
                else:
                    host = line.split('/')[2]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 80
            self._host = host
            self._port = int(port)
        return self._host, self._port
 
    @property
    def data(self):
        """
        返回头部数据
        :return:
        """
        return self._header
 
    def is_ssl(self):
        """
        判断是否为 https协议
        :return:
        """
        if self.get_method() == b'CONNECT':
            return True
        return False
 
    def __repr__(self):
        return str(self._header.decode("utf8"))
 
def communicate(sock1, sock2):
    """
    socket之间的数据交换
    :param sock1:
    :param sock2:
    :return:
    """

    try:
        while 1:       # 死循环
            data = sock1.recv(1024)
            # print(data.decode('utf-8'))
            # print(data)
            if not data:
                return
            sock2.sendall(data)
    except Exception as e:
        # print(e)
        pass
 
 
def handle(client):  # 每次创建的进程
    """
    处理连接进来的客户端
    :param client:
    :return:
    """
    timeout = 6
    client.settimeout(timeout)
    header = Header(client)  # 头部的初始化
    if not header.data:
        client.close()
        return
    # 输出头部信息
    print("==========>>>>>>>>> ", header.get_host_info()[0], header.get_host_info()[1], header.get_method().decode('utf-8'))
    # print(header._header.decode("utf8"))

    # print(header.data)

    flag = 1
    while flag:
        try:
            """连接，设置代理"""
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 连接
            proxy = enable_ip() # 获取随机一个代理IP:port
            proxyHost,proxyPort = proxy.split(":")[0],int(proxy.split(":")[1]) #IP,port
            socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5,addr=proxyHost,port=int(proxyPort)) # 设置全局代理
            socket.socket = socks.socksocket
            server.settimeout(timeout)
            server.connect(header.get_host_info()) # 获取目标主机的ip和端口
            print("socks5: ", proxyHost, proxyPort)
            flag = 0
        except Exception as e:
            print(e)
    try:
        if header.is_ssl():  # 判断是否是http协议
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client.sendall(data)  # 然后再次开启进程
            _thread.start_new_thread(communicate, (client, server))
        else:
            server.sendall(header.data)
        communicate(server, client)
    except Exception as e:
        # print(e)
        server.close()
        client.close()


def serve(ip, port):
    """
    代理服务
    :param ip:
    :param port:
    :return:

    """

    """设置sock连接，绑定ip跟端口，作死循环,循环里创建新线程"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(100)
    print('proxy start...', port)
    while True:
        conn, addr = s.accept()  # socket.accept
        if conn:  # 这个应该是如果存在，创建进程handle
            _thread.start_new_thread(handle, (conn,))
def enable_ip():
    """
    将爬取的代理池txt，放入ip[]中，随机取一个ip并返回
    (如果要换IP，也是从这里去修改，无论是从网上拿还是咋的)
    """
    import random
    ip = []
    fr =open("alive.txt",'r')
    lines = fr.readlines()
    for line in lines:
        ip.append(line)
    tag = random.randint(0,len(ip)-1)		#随机获取当前可用代理池的ip
    return ip[tag]
 
if __name__ == '__main__':
    """
    所以其实代码就那么点，应该是python好实现。在check.py文件中检查IP等内容;server.py执行功能代码
    使用burp绑定端口和设置代理。
    socket就是一种协议，可以上网用的，跟http似的，所以我们可以使用其他IP走这个协议，实现代理
    通信原理图放在readme的开头了
    代理的流程如下：

1.localhost:1080经过sock5协议后，就知道要访问google了
2.local程序会把流量加密，然后把普通的TCP流量发往海外服务器；
3.海外服务器收到请求后，解密得到要访问google
4.海外服务器请求google后把得到的数据加密返回给local
5.local解密返回给browser。
    """
    IP = "0.0.0.0"
    PORT = 8082
    serve(IP, PORT)
