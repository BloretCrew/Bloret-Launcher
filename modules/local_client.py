import socket
import threading
import select
import time
import requests
from modules.log import log

class LocalClient:
    def __init__(self):
        self.is_connected = False
        self.is_running = True
        self.server_socket = None
        self.remote_host = 'pcfs.top'  # 公网服务器地址
        self.remote_port = 5000  # API端口
        self.local_host = '127.0.0.1'
        self.local_port = 8080  # 本地服务端口
        self.forwarding_thread = None
        self.service_port = None  # 服务端分配的用于数据转发的端口

    def set_config(self, remote_host: str, remote_port: int, local_host: str, local_port: int):
        """设置客户端配置"""
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port

    def register_with_server(self, server_api_url: str, token: str, local_port: int) -> bool:
        """向服务端注册并获取远程端口"""
        try:
            response = requests.get(f"{server_api_url}/client", params={
                'token': token,
                'port': local_port
            })
            
            if response.status_code == 200:
                import json
                data = response.json()
                if data.get('success'):
                    self.service_port = data['remote_port']
                    log(f'成功注册到服务端，分配的远程端口: {self.service_port}')
                    return True
                else:
                    log(f'服务端返回错误: {data.get("message", "未知错误")}')
                    return False
            else:
                log(f'注册失败，HTTP状态码: {response.status_code}')
                return False
        except Exception as e:
            log(f'注册到服务端时发生异常: {str(e)}')
            return False

    def connect_to_server(self) -> bool:
        """连接到公网服务器的数据转发端口"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置连接超时
            self.server_socket.settimeout(10)
            self.server_socket.connect((self.remote_host, self.service_port))
            self.is_connected = True
            log(f'已连接到公网服务器 {self.remote_host}:{self.service_port}')
            return True
        except Exception as e:
            log(f'连接服务器失败: {str(e)}')
            return False

    def forward_data(self, remote_socket: socket.socket, local_socket: socket.socket):
        """双向数据转发"""
        try:
            while self.is_connected and self.is_running:
                try:
                    # 使用select监听两个socket的可读事件，设置超时避免阻塞
                    readable, _, _ = select.select([remote_socket, local_socket], [], [], 1)
                    if not readable:
                        continue

                    for sock in readable:
                        try:
                            data = sock.recv(4096)
                            if not data:
                                # 连接已关闭
                                self.is_connected = False
                                self.is_running = False
                                break

                            # 发送数据到另一端
                            if sock == remote_socket:
                                # 从服务端接收到的数据转发给本地服务
                                local_socket.sendall(data)
                            else:
                                # 从本地服务接收到的数据转发给服务端
                                remote_socket.sendall(data)
                        except ConnectionResetError:
                            # 远程主机强迫关闭连接，这是正常现象，不需要记录错误日志
                            log("远程主机关闭了连接")
                            self.is_connected = False
                            self.is_running = False
                            break
                        except Exception as e:
                            # 其他异常记录日志
                            log(f'数据转发错误: {str(e)}')
                            self.is_connected = False
                            self.is_running = False
                            break
                except Exception as e:
                    if self.is_running:
                        log(f'转发循环错误: {str(e)}')
                    self.is_running = False
        except Exception as e:
            log(f'数据转发错误: {str(e)}')
        finally:
            self.is_connected = False
            self.is_running = False
            try:
                remote_socket.close()
            except:
                pass
            try:
                local_socket.close()
            except:
                pass
            log('连接已关闭')

    def start_forwarding(self) -> bool:
        """开始端口转发"""
        # 先向服务端注册
        if not self.register_with_server(
            f"http://{self.remote_host}:{self.remote_port}", 
            "Bloret-PCFS-Token-Now-Rhedar-Detrital", 
            self.local_port
        ):
            log("无法注册到服务端")
            return False
            
        self.is_running = True
        
        # 连接到本地服务
        try:
            local_socket = self.create_local_socket()
        except Exception as e:
            log(f'无法连接到本地服务: {str(e)}')
            return False
        
        if not self.connect_to_server():
            try:
                local_socket.close()
            except:
                pass
            return False

        # 启动转发线程
        self.forwarding_thread = threading.Thread(target=self.forward_data,
                                                  args=(self.server_socket, local_socket),
                                                  daemon=True)
        self.forwarding_thread.start()
        return True

    def create_local_socket(self) -> socket.socket:
        """创建到本地服务的连接"""
        try:
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置连接超时
            local_socket.settimeout(5)
            local_socket.connect((self.local_host, self.local_port))
            log(f'已连接到本地服务 {self.local_host}:{self.local_port}')
            return local_socket
        except Exception as e:
            log(f'连接本地服务失败: {str(e)}')
            log(f'请确保本地服务正在 {self.local_host}:{self.local_port} 端口运行')
            log(f'提示：您可以使用 "python -m http.server {self.local_port}" 启动一个测试服务器')
            raise

    def stop_forwarding(self):
        """停止端口转发"""
        self.is_running = False
        self.is_connected = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                log(f'关闭服务器连接错误: {str(e)}')
        if self.forwarding_thread and self.forwarding_thread.is_alive():
            self.forwarding_thread.join(timeout=1)
        log('端口转发已停止')


def OnlineClient(localhost_port=8080):
    """
    启动内网穿透客户端
    :param localhost_port: 本地网站服务端口（默认8080）
    :return: 连接地址字符串
    """
    client = LocalClient()
    client.set_config(
        remote_host='pcfs.top',          # 公网服务器地址
        remote_port=5000,                # 服务端API端口，用于客户端注册
        local_host='127.0.0.1',          # 本地服务IP
        local_port=localhost_port        # 本地网站服务端口
    )
    if client.start_forwarding():
        # 返回连接地址（注意：实际访问端口由服务端分配）
        if client.service_port:
            return f"{client.remote_host}:{client.service_port}"
        else:
            return f"{client.remote_host}"  # fallback
    else:
        return None

# if __name__ == '__main__':
#     # 示例用法
#     client = LocalClient()
#     client.set_config(
#         remote_host='pcfs.top',  # 需要替换为公网服务器的实际IP
#         remote_port=5000,            # 与服务器的 remote_port 一致
#         local_host='127.0.0.1',      # 本地服务IP（通常不需要更改）
#         local_port=8080              # 本地服务端口（需要与服务器的 local_port 一致）
#     )
#     
#     if client.start_forwarding():
#         log('端口转发已启动，按Ctrl+C停止...')
#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             client.stop_forwarding()
#     else:
#         log('端口转发启动失败')