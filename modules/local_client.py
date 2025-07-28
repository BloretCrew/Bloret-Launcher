import socket
import threading
import select
import logging
import time
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalClient:
    def __init__(self):
        self.is_connected = False
        self.server_socket = None
        self.remote_host = ''  # 公网服务器地址
        self.remote_port = 8080
        self.local_host = '127.0.0.1'
        self.local_port = 5000
        self.forwarding_thread = None

    def set_config(self, remote_host: str, remote_port: int, local_host: str, local_port: int):
        """设置客户端配置"""
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port

    def connect_to_server(self) -> bool:
        """连接到公网服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.remote_host, self.remote_port))
            self.is_connected = True
            logger.info(f'已连接到公网服务器 {self.remote_host}:{self.remote_port}')
            return True
        except Exception as e:
            logger.error(f'连接服务器失败: {str(e)}')
            return False

    def forward_data(self, remote_socket: socket.socket, local_socket: socket.socket):
        """双向数据转发"""
        try:
            while self.is_connected:
                readable, _, _ = select.select([remote_socket, local_socket], [], [], 1)
                if not readable:
                    continue

                for sock in readable:
                    data = sock.recv(4096)
                    if not data:
                        self.is_connected = False
                        break

                    if sock == remote_socket:
                        local_socket.sendall(data)
                    else:
                        remote_socket.sendall(data)
        except Exception as e:
            logger.error(f'数据转发错误: {str(e)}')
        finally:
            remote_socket.close()
            local_socket.close()
            self.is_connected = False
            logger.info('连接已关闭')

    def start_forwarding(self) -> bool:
        """开始端口转发"""
        if not self.connect_to_server():
            return False

        # 启动转发线程
        self.forwarding_thread = threading.Thread(target=self.forward_data,
                                                  args=(self.server_socket, self.create_local_socket()),
                                                  daemon=True)
        self.forwarding_thread.start()
        return True

    def create_local_socket(self) -> socket.socket:
        """创建到本地服务的连接"""
        try:
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.connect((self.local_host, self.local_port))
            logger.info(f'已连接到本地服务 {self.local_host}:{self.local_port}')
            return local_socket
        except Exception as e:
            logger.error(f'连接本地服务失败: {str(e)}')
            raise

    def stop_forwarding(self):
        """停止端口转发"""
        self.is_connected = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f'关闭服务器连接错误: {str(e)}')
        if self.forwarding_thread and self.forwarding_thread.is_alive():
            self.forwarding_thread.join(timeout=1)
        logger.info('端口转发已停止')


def OnlineClient(localhost_port):
    client = LocalClient()
    client.set_config(
        remote_host='pcfs.top',  # 需要替换为公网服务器的实际IP
        remote_port=8080,            # 与服务器的 remote_port 一致
        local_host='127.0.0.1',      # 本地服务IP（通常不需要更改）
        local_port=localhost_port    # 本地服务端口（需要与服务器的 local_port 一致）
    )
    client.start_forwarding()

# if __name__ == '__main__':
#     # 示例用法
#     client = LocalClient()
#     client.set_config(
#         remote_host='pcfs.top',  # 需要替换为公网服务器的实际IP
#         remote_port=8080,            # 与服务器的 remote_port 一致
#         local_host='127.0.0.1',      # 本地服务IP（通常不需要更改）
#         local_port=2              # 本地服务端口（需要与服务器的 local_port 一致）
#     )
    
#     if client.start_forwarding():
#         logger.info('端口转发已启动，按Ctrl+C停止...')
#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             client.stop_forwarding()
#     else:
#         logger.error('端口转发启动失败')