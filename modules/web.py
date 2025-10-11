import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import logging
import os
import json
from modules.plugin import addPlugin
from modules.win11toast import toast

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 用于存储待确认的插件信息
pending_plugins = {}

class WebRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 处理 /login/Bloret-PassPort 路径
        if self.path.startswith('/login/Bloret-PassPort'):
            # 解析查询参数
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # 获取 code 参数
            code = query_params.get('code', [None])[0]
            
            if code:
                # 向验证服务器发送请求
                verify_url = "http://pcfs.eno.ink:20000/app/verify"
                params = {
                    'app_id': 'BloretLauncher',
                    'app_secret': 's4d56f4a68sd46g54asd46f54a5dsf654asdf546',
                    'code': code
                }
                
                try:
                    response = requests.get(verify_url, params=params)
                    response_data = response.text
                    
                    # 输出到控制台
                    print(f"OAuth verification response: {response_data}")
                    logger.info(f"OAuth verification response: {response_data}")
                    
                    # 解析响应数据并保存到 config.json
                    try:
                        user_data = json.loads(response_data)
                        if isinstance(user_data, dict) and 'username' in user_data and 'email' in user_data:
                            # 读取现有配置
                            try:
                                with open('config.json', 'r', encoding='utf-8') as f:
                                    config_data = json.load(f)
                            except FileNotFoundError:
                                config_data = {}
                            
                            # 更新Bloret Passport用户信息
                            config_data['Bloret_PassPort_Login'] = True
                            config_data['Bloret_PassPort_UserName'] = user_data['username']
                            config_data['Bloret_PassPort_PassWord'] = user_data.get('apptoken', '')
                            
                            # 保存配置到文件
                            with open('config.json', 'w', encoding='utf-8') as f:
                                json.dump(config_data, f, ensure_ascii=False, indent=4)
                                
                            logger.info(f"User data saved to config.json: {user_data['username']}")
                    except json.JSONDecodeError:
                        logger.error("Failed to parse OAuth response as JSON")
                    
                    # 返回成功的网页页面
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.generate_success_page()
                    self.wfile.write(html_content.encode('utf-8'))
                    
                    toast(f'您已以 {user_data["username"]} 登录', f'登录后可使用 Bloret PassPort 服务，例如同步 Minecraft 登录信息到云端等功能')
                    
                except Exception as e:
                    logger.error(f"Error during OAuth verification: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.generate_error_page(f"Error during OAuth verification: {str(e)}")
                    self.wfile.write(html_content.encode('utf-8'))
            else:
                # code 参数缺失，但仍然显示成功页面
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html_content = self.generate_success_page()
                self.wfile.write(html_content.encode('utf-8'))
        elif self.path.startswith('/plugin/confirm'):
            # 处理插件安装确认页面
            try:
                # 解析查询参数
                parsed_path = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_path.query)
                
                # 获取插件参数
                plugin_name = query_params.get('name', ['Unknown Plugin'])[0]
                plugin_download = query_params.get('download', [''])[0]
                plugin_master = query_params.get('master', ['Unknown Author'])[0]
                plugin_version = query_params.get('version', ['Unknown Version'])[0]
                
                # 生成确认页面
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html_content = self.generate_plugin_confirmation_page({
                    'name': plugin_name,
                    'download': plugin_download,
                    'master': plugin_master,
                    'version': plugin_version
                })
                self.wfile.write(html_content.encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error generating plugin confirmation page: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html_content = self.generate_error_page(f"Error generating plugin confirmation page: {str(e)}")
                self.wfile.write(html_content.encode('utf-8'))
        elif self.path.startswith('/plugin/install'):
            # 处理插件安装请求
            try:
                # 解析查询参数
                parsed_path = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_path.query)
                
                # 获取插件下载链接
                plugin_download = query_params.get('download', [None])[0]
                
                # 获取插件名称
                plugin_name = query_params.get('name')
                
                if plugin_download:
                    print(f"直接在当前线程中执行插件安装并返回结果: 安装插件 {plugin_name}")
                    # 直接在当前线程中执行插件安装并返回结果
                    self.install_plugin_and_respond(plugin_download, plugin_name)
                else:
                    # download 参数缺失
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.generate_error_page("Missing 'download' parameter")
                    self.wfile.write(html_content.encode('utf-8'))
                    
            except Exception as e:
                logger.error(f"Error during plugin installation: {e}")
                # 错误处理在install_plugin方法中完成
                pass
        elif self.path.startswith('/plugin/add'):
            # 处理 /plugin/add 路径 - 合并确认、安装和添加功能
            try:
                # 解析查询参数
                parsed_path = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_path.query)
                
                # 获取参数
                list_url = query_params.get('list', [None])[0]
                plugin_download = query_params.get('download', [None])[0]
                plugin_name = query_params.get('name', [None])[0]
                plugin_master = query_params.get('master', [None])[0]
                plugin_version = query_params.get('version', [None])[0]
                action = query_params.get('action', ['confirm'])[0]  # 默认为确认操作
                
                # 根据不同操作执行不同逻辑
                if action == 'confirm' and (list_url or (plugin_name and plugin_download)):
                    # 显示插件安装确认页面
                    if list_url:
                        # 从list_url获取插件信息
                        response = requests.get(list_url)
                        response.raise_for_status()
                        plugin = response.json()
                    else:
                        # 使用查询参数中的插件信息
                        plugin = {
                            'name': plugin_name,
                            'download': plugin_download,
                            'master': plugin_master or 'Unknown Author',
                            'version': plugin_version or 'Unknown Version'
                        }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.generate_plugin_confirmation_page(plugin)
                    self.wfile.write(html_content.encode('utf-8'))
                    
                elif action == 'install' and plugin_download:
                    # 直接在当前线程中执行插件安装并返回结果
                    self.install_plugin_and_respond(plugin_download, plugin_name)
                    
                else:
                    # 缺少必要参数
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    html_content = self.generate_error_page("Missing required parameters")
                    self.wfile.write(html_content.encode('utf-8'))
                    
            except Exception as e:
                logger.error(f"Error processing plugin add request: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html_content = self.generate_error_page(f"Error processing plugin request: {str(e)}")
                self.wfile.write(html_content.encode('utf-8'))
        elif self.path == '/index.css':
            # 提供CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'index.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"CSS file not found")
        else:
            # 未找到的路径
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not Found")

    def install_plugin_and_respond(self, plugin_url, plugin_name):
        """安装插件并返回结果页面"""
        try:
            # 运行 addPlugin 函数
            result = addPlugin(plugin_url, plugin_name)
            logger.info(f"Plugin installation completed for {plugin_url} with result: {result}")
            
            # 根据结果发送成功或失败页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            if result:
                html_content = self.generate_install_success_page()
            else:
                html_content = self.generate_error_page("插件安装失败")
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error during plugin installation: {e}")
            # 发送错误页面
            self.send_response(500)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.generate_error_page(f"Error during plugin installation: {str(e)}")
            self.wfile.write(html_content.encode('utf-8'))

    def generate_success_page(self):
        """生成授权成功的页面"""
        return '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>授权成功</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('http://pcfs.eno.ink:20009/api/img/Takanashi-Hoshino?ratio=16_9');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .container {
            background: rgba(255, 255, 255, 0.35);
            border-radius: 18px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18), 0 1.5px 8px 0 rgba(255, 255, 255, 0.25) inset;
            border: 1.5px solid rgba(255, 255, 255, 0.45);
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            max-width: 500px;
            width: 80%;
        }
        h1 {
            color: white;
            font-weight: 500;
            margin-bottom: 20px;
            font-size: 28px;
        }
        p {
            font-size: 18px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
            margin: 10px 0;
        }
        .icon {
            font-size: 48px;
            margin-bottom: 20px;
            color: white;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✓</div>
        <h1>授权成功</h1>
        <p>您的 Bloret Passport 账户已成功授权</p>
        <p>请返回 Bloret Launcher 继续操作</p>
    </div>
</body>
</html>
        '''

    def generate_plugin_confirmation_page(self, plugin, list_url=None):
        """生成插件安装确认页面"""
        plugin_name = plugin.get('name', 'Unknown Plugin')
        plugin_master = plugin.get('master', 'Unknown Author')
        plugin_version = plugin.get('version', 'Unknown Version')
        plugin_download = plugin.get('download', '')
        
        # 构造安装链接 - 使用新的合并路由
        install_params = {
            'action': 'install',
            'download': plugin_download,
            'name': plugin_name
        }
        install_url = f"/plugin/add?{urllib.parse.urlencode(install_params)}"
        
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装确认</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('http://pcfs.eno.ink:20009/api/img/Takanashi-Hoshino?ratio=16_9');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.35);
            border-radius: 18px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18), 0 1.5px 8px 0 rgba(255, 255, 255, 0.25) inset;
            border: 1.5px solid rgba(255, 255, 255, 0.45);
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            max-width: 500px;
            width: 80%;
        }}
        h1 {{
            color: white;
            font-weight: 500;
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            font-size: 18px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
            margin: 10px 0;
        }}
        .warning {{
            color: #ffcc00;
            font-weight: bold;
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 204, 0, 0.2);
            border-radius: 10px;
            font-size: 16px;
        }}
        .plugin-info {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
        }}
        .plugin-info div {{
            margin: 10px 0;
        }}
        .icon {{
            font-size: 48px;
            margin-bottom: 20px;
            color: white;
        }}
        .btn {{
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }}
        .btn.cancel {{
            background-color: #f44336;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .container {{
            animation: fadeIn 0.5s ease-out forwards;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">ⓘ</div>
        <h1>插件安装确认</h1>
        <div class="plugin-info">
            <div><strong>插件名称:</strong> {plugin_name}</div>
            <div><strong>插件作者:</strong> {plugin_master}</div>
            <div><strong>插件版本:</strong> {plugin_version}</div>
        </div>
        <div class="warning">
            警告：插件可以访问 Bloret Launcher 的所有内容，请谨慎安装！
        </div>
        <p>您确定要安装此插件吗？</p>
        <a href="{install_url}" class="btn">确认安装</a>
        <button class="btn cancel" onclick="window.close()">取消</button>
    </div>
    
    <script>
        // 如果用户点击确认安装按钮，显示正在安装页面
        document.querySelector('.btn').addEventListener('click', function() {{
            // 创建正在安装的页面
            document.body.innerHTML = `
                <div class="container">
                    <div class="spinner"></div>
                    <h1>插件安装中</h1>
                    <p>正在安装插件，请稍候...</p>
                    <p>安装完成后您可以关闭此页面</p>
                </div>
            `;
        }});
    </script>
</body>
</html>
        '''

    def generate_installing_page(self):
        """生成正在安装插件的页面，使用 Apple Liquid Glass 设计"""
        return '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装中</title>
    <link rel="stylesheet" href="/index.css">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('http://pcfs.eno.ink:20009/api/img/Takanashi-Hoshino?ratio=16_9');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .container {
            background: rgba(255, 255, 255, 0.35);
            border-radius: 18px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18), 0 1.5px 8px 0 rgba(255, 255, 255, 0.25) inset;
            border: 1.5px solid rgba(255, 255, 255, 0.45);
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            max-width: 500px;
            width: 80%;
        }
        h1 {
            color: white;
            font-weight: 500;
            margin-bottom: 20px;
            font-size: 28px;
        }
        p {
            font-size: 18px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
            margin: 10px 0;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h1>插件安装中</h1>
        <p>正在安装插件，请稍候...</p>
        <p>安装完成后您可以关闭此页面</p>
    </div>
</body>
</html>
        '''

    def generate_install_success_page(self):
        """生成插件安装成功页面"""
        return '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装成功</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('http://pcfs.eno.ink:20009/api/img/Takanashi-Hoshino?ratio=16_9');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .container {
            background: rgba(255, 255, 255, 0.35);
            border-radius: 18px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18), 0 1.5px 8px 0 rgba(255, 255, 255, 0.25) inset;
            border: 1.5px solid rgba(255, 255, 255, 0.45);
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            max-width: 500px;
            width: 80%;
        }
        h1 {
            color: white;
            font-weight: 500;
            margin-bottom: 20px;
            font-size: 28px;
        }
        p {
            font-size: 18px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
            margin: 10px 0;
        }
        .icon {
            font-size: 48px;
            margin-bottom: 20px;
            color: white;
        }
        .btn {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }
        .btn:hover {
            opacity: 0.9;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✓</div>
        <h1>插件安装成功</h1>
        <p>插件已成功安装到您的 Bloret Launcher 中</p>
        <p>您可以关闭此页面并返回 Bloret Launcher 使用新插件</p>
    </div>
</body>
</html>
        '''

    def generate_error_page(self, error_message):
        """生成错误页面"""
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>授权失败</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #ea6666 0%, #a24b4b 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('http://pcfs.eno.ink:20009/api/img/Takanashi-Hoshino?ratio=16_9');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.35);
            border-radius: 18px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18), 0 1.5px 8px 0 rgba(255, 255, 255, 0.25) inset;
            border: 1.5px solid rgba(255, 255, 255, 0.45);
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            max-width: 500px;
            width: 80%;
        }}
        h1 {{
            color: white;
            font-weight: 500;
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            font-size: 18px;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1.6;
            margin: 10px 0;
        }}
        .error {{
            color: rgba(255, 255, 255, 0.95);
            font-weight: bold;
            margin: 20px 0;
            padding: 15px;
            background: rgba(244, 67, 54, 0.2);
            border-radius: 10px;
            font-size: 16px;
        }}
        .icon {{
            font-size: 48px;
            margin-bottom: 20px;
            color: white;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .container {{
            animation: fadeIn 0.5s ease-out forwards;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✗</div>
        <h1>授权失败</h1>
        <p>在处理您的 Bloret Passport 授权时发生错误</p>
        <div class="error">{error_message}</div>
        <p>请关闭此页面并返回 Bloret Launcher 重试</p>
    </div>
</body>
</html>
        '''

    def log_message(self, format, *args):
        # 重写日志消息格式
        logger.info("%s - - [%s] %s\n" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format % args))

def start_server():
    """启动Web服务器"""
    server_address = ('localhost', 25252)
    httpd = HTTPServer(server_address, WebRequestHandler)
    logger.info("Starting web server on port 25252...")
    httpd.serve_forever()

# 当模块被导入时启动服务器
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()