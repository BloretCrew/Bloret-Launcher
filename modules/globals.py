server_ip = "http://pcfs.eno.ink:2/" # Bloret Launcher Server 服务器地址 （尾部带斜杠）
ver_id_main = []
ver_id_short = []
ver_id = [] 
ver_url = {}
ver_id_long = []
ver_id_bloret = ['1.21.7', '1.21.8']
set_list = []
set_list.append("你还未安装任何版本哦，请前往下载页面安装")
BL_update_text = ""
BL_latest_ver = 0
threads = []
icon = {'src': 'bloret.ico','placement': 'appLogoOverride'}
minecraft_list = []
tabbar = None
isdarktheme = False
LM_Download_Way_list = ["1.21.8","1.21.7"]

config_path = ''

import os, sys

if sys.platform == 'win32':
    datapath = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Bloret-Launcher')
elif sys.platform == 'darwin':
    datapath = os.path.expanduser('~/Library/Application Support/Bloret-Launcher')
else:
    datapath = os.path.expanduser('~/.local/share/Bloret-Launcher')
minecraft_dir = ""
BLtips = []
BL_Activity = {}
