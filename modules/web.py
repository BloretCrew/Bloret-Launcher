import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import logging
import os
import json
from modules.plugin import addPlugin
from modules.win11toast import toast
import modules.globals as BLglobals
from modules.log import log

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
                verify_url = f"{BLglobals.server_ip}:20000/app/verify"
                params = {
                    'app_id': 'BloretLauncher',
                    'app_secret': 's4d56f4a68sd46g54asd46f54a5dsf654asdf546',
                    'code': code
                }
                
                try:
                    # 优先使用配置的 server_ip (可能是代理地址)
                    verify_url = f"{BLglobals.server_ip}:20000/app/verify"
                    logger.info(f"Trying verify_url: {verify_url}")
                    response = requests.get(verify_url, params=params)
                    
                    # 如果响应状态码不是 200 或内容为空/非 JSON，尝试直连 IP:20000
                    # 注意：这里我们通过解析 server_ip 来获取 IP 地址
                    if response.status_code != 200 or not response.text.strip().startswith('{'):
                         logger.warning(f"Primary verify failed. Status: {response.status_code}, Body: {response.text[:100]}...")
                         
                         # 尝试提取 IP 地址并构建直连 URL
                         # 假设 BLglobals.server_ip 格式为 http://IP:PORT/ 或 http://DOMAIN:PORT/
                         try:
                             from urllib.parse import urlparse
                             parsed_uri = urlparse(BLglobals.server_ip)
                             host = parsed_uri.hostname
                             if host:
                                 fallback_url = f"http://{host}:20000/app/verify"
                                 logger.info(f"Trying fallback_url: {fallback_url}")
                                 response = requests.get(fallback_url, params=params)
                         except Exception as ex:
                             logger.error(f"Failed to construct fallback URL: {ex}")

                    response_data = response.text
                    
                    # 输出到控制台
                    print(f"OAuth verification response status: {response.status_code}")
                    print(f"OAuth verification response body: {response_data}")
                    logger.info(f"OAuth verification response status: {response.status_code}")
                    logger.info(f"OAuth verification response body: {response_data}")
                    
                    # 解析响应数据并保存到 config.json
                    try:
                        user_data = json.loads(response_data)
                        logger.info(f"OAuth response user_data: {user_data}")
                        if isinstance(user_data, dict) and 'username' in user_data and 'email' in user_data:
                            # 读取现有配置
                            try:
                                with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                                    config_data = json.load(f)
                            except FileNotFoundError:
                                config_data = {}
                            
                            # 更新Bloret Passport用户信息
                            config_data['Bloret_PassPort_Login'] = True
                            config_data['Bloret_PassPort_UserName'] = user_data['username']
                            config_data['Bloret_PassPort_PassWord'] = user_data.get('apptoken', '')
                            # avatar field may not exist; still write key even if empty
                            avatar_val = user_data.get('avatar', '')
                            config_data['Bloret_PassPort_Avatar'] = avatar_val
                            logger.info(f"Avatar value from server: '{avatar_val}'")
                            # 保存配置到文件
                            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                                json.dump(config_data, f, ensure_ascii=False, indent=4)
                                
                            logger.info(f"User data saved to config.json: {user_data['username']}")

                            # 返回成功的网页页面
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html; charset=utf-8')
                            self.end_headers()
                            
                            html_content = self.generate_success_page()
                            self.wfile.write(html_content.encode('utf-8'))
                            
                            toast(f'您已以 {user_data["username"]} 登录', f'登录后可使用 Bloret PassPort 服务，例如同步 Minecraft 登录信息到云端等功能')
                        else:
                            raise ValueError("Invalid user data format")

                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse OAuth response: {e}")
                        raise

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
        elif self.path == '/sync/Minecraft_Account':
            # 处理 /sync/Minecraft_Account 路径
            try:
                # 1. 从 config.json 读取用户信息
                with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 检查是否已登录 Passport
                if not config_data.get('Bloret_PassPort_Login'):
                    raise Exception("请先登录 Bloret Passport")

                username = config_data.get('Bloret_PassPort_UserName')
                user_token = config_data.get('Bloret_PassPort_PassWord')

                # 2. 向验证服务器发送请求获取 Minecraft 账户列表
                verify_url = f"{BLglobals.server_ip}:20000/app/MinecraftAccounts"
                params = {
                    'app_id': 'BloretLauncher',
                    'app_secret': 's4d56f4a68sd46g54asd46f54a5dsf654asdf546',
                    'user': username,
                    'usertoken': user_token
                }
                
                response = requests.get(verify_url, params=params)
                
                if response.status_code != 200:
                     raise Exception(f"服务器返回状态码: {response.status_code}")

                try:
                    api_result = response.json()
                except Exception:
                    logger.error(f"Invalid JSON response from server: {response.text}")
                    raise Exception(f"服务器返回无效的 JSON 数据")
                
                if api_result.get('status') == 'success':
                    # 3. 更新 config.json 中的 MinecraftAccount 字段
                    accounts = api_result.get('accounts', [])
                    
                    # 获取旧的 chosen 值，如果不存在或越界，则默认为 0
                    old_minecraft_account = config_data.get('MinecraftAccount', {})
                    old_chosen = old_minecraft_account.get('chosen', 0)
                    
                    # 如果之前的 chosen 索引在新列表中仍然有效，则保持不变；否则重置为 0
                    new_chosen = old_chosen if 0 <= old_chosen < len(accounts) else (0 if accounts else -1)

                    config_data['MinecraftAccount'] = {
                        "logined": True if accounts else False,
                        "chosen": new_chosen,
                        "accounts": accounts
                    }
                    
                    # 保存配置
                    with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=4)
                    
                    log(f"Minecraft accounts synced: {len(accounts)} accounts found.")
                    
                    # 4. 执行重定向跳转回 Passport 官网
                    self.send_response(302)
                    self.send_header('Location', 'https://passport.bloret.net/')
                    self.end_headers()
                    
                    toast('已从 Bloret PassPort 同步账户', f'已成功同步 {len(accounts)} 个账户到本地。')
                else:
                    message = api_result.get('message', '未知错误')
                    raise Exception(f"服务器返回错误: {message}")

            except Exception as e:
                logger.error(f"Error during Minecraft account sync: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                html_content = self.generate_error_page(f"同步失败: {str(e)}")
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
        elif self.path == '/fluent.css':
            # 提供Fluent Design CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'fluent.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving fluent CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Fluent CSS file not found")
        elif self.path == '/plugin-confirm.css':
            # 提供插件确认页面CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'plugin-confirm.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving plugin confirm CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Plugin confirm CSS file not found")
        elif self.path == '/installing.css':
            # 提供安装中页面CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'installing.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving installing CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Installing CSS file not found")
        elif self.path == '/install-success.css':
            # 提供安装成功页面CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'install-success.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving install success CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Install success CSS file not found")
        elif self.path == '/error.css':
            # 提供错误页面CSS文件
            try:
                css_path = os.path.join(os.path.dirname(__file__), 'web', 'error.css')
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(css_content.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error serving error CSS file: {e}")
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Error CSS file not found")
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

    def generate_success_page(self, username=None):
        """生成授权成功页面 - Microsoft Fluent2 Design"""
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>授权成功</title>
    <link rel="stylesheet" href="/fluent.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon"></div>
        <h1 class="fluent-title">授权成功</h1>
        <p class="fluent-text">您已成功登录 Bloret Passport</p>
        {f'<p class="fluent-text">欢迎回来，{username}！</p>' if username else ''}
        <p class="fluent-text">现在您可以关闭此页面并返回 Bloret Launcher</p>
        <button class="fluent-btn fluent-btn-primary" onclick="window.close()">关闭页面</button>
    </div>
</body>
</html>
        '''

    def generate_plugin_confirmation_page(self, plugin, list_url=None):
        """生成插件安装确认页面 - Microsoft Fluent2 Design"""
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
    <link rel="stylesheet" href="/plugin-confirm.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon">ⓘ</div>
        <h1 class="fluent-title">插件安装确认</h1>
        
        <div class="fluent-info-card">
            <div class="info-row">
                <span class="info-label">插件名称:</span>
                <span class="info-value">{plugin_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">插件作者:</span>
                <span class="info-value">{plugin_master}</span>
            </div>
            <div class="info-row">
                <span class="info-label">插件版本:</span>
                <span class="info-value">{plugin_version}</span>
            </div>
        </div>
        
        <div class="fluent-warning">
            警告：插件可以访问 Bloret Launcher 的所有内容，请谨慎安装！
        </div>
        
        <p class="fluent-text">您确定要安装此插件吗？</p>
        
        <div class="fluent-button-group">
            <a href="{install_url}" class="fluent-btn fluent-btn-primary">确认安装</a>
            <button class="fluent-btn fluent-btn-secondary" onclick="window.close()">取消</button>
        </div>
    </div>
    
    <script>
        // 如果用户点击确认安装按钮，显示正在安装页面
        document.querySelector('.fluent-btn-primary').addEventListener('click', function(e) {{
            e.preventDefault();
            // 创建正在安装的页面
            document.body.innerHTML = `
                <div class="fluent-card">
                    <div class="fluent-icon" style="background: linear-gradient(135deg, var(--fluent-primary), #106ebe);">
                        <div class="spinner"></div>
                    </div>
                    <h1 class="fluent-title">插件安装中</h1>
                    <p class="fluent-text">正在安装插件，请稍候...</p>
                    <p class="fluent-text">安装完成后您可以关闭此页面</p>
                </div>
                <style>
                    .spinner {{
                        width: 24px;
                        height: 24px;
                        border: 3px solid rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        border-top: 3px solid white;
                        animation: spin 1s linear infinite;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
            `;
            // 延迟跳转，让用户看到安装中状态
            setTimeout(() => {{
                window.location.href = '{install_url}';
            }}, 800);
        }});
    </script>
</body>
</html>
        '''

    def generate_installing_page(self):
        """生成插件安装中页面 - Microsoft Fluent2 Design"""
        return '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装中</title>
    <link rel="stylesheet" href="/installing.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon">
            <div class="fluent-spinner"></div>
        </div>
        <h1 class="fluent-title">插件安装中</h1>
        <p class="fluent-text">正在安装插件，请稍候...</p>
        <p class="fluent-text">安装完成后您可以关闭此页面</p>
        <div class="fluent-progress">
            <div class="fluent-progress-bar"></div>
        </div>
    </div>
</body>
</html>
        '''

    def generate_install_success_page(self, plugin_name):
        """生成插件安装成功页面 - Microsoft Fluent2 Design"""
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装成功</title>
    <link rel="stylesheet" href="/install-success.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon"></div>
        <h1 class="fluent-title">插件安装成功</h1>
        <p class="fluent-text">插件 {plugin_name} 已成功安装！</p>
        <p class="fluent-text">您现在可以在 Bloret Launcher 中使用此插件了。</p>
        <button class="fluent-btn fluent-btn-success" onclick="window.close()">关闭页面</button>
    </div>
</body>
</html>
        '''

    def generate_error_page(self, error_message):
        """生成错误页面 - Microsoft Fluent2 Design"""
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>插件安装失败</title>
    <link rel="stylesheet" href="/error.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon"></div>
        <h1 class="fluent-title">插件安装失败</h1>
        <p class="fluent-text">抱歉，插件安装过程中出现错误。</p>
        <div class="fluent-error-card">
            <div class="fluent-error-message">{error_message}</div>
        </div>
        <p class="fluent-text">请稍后重试或联系插件作者。</p>
        <button class="fluent-btn fluent-btn-error" onclick="window.close()">关闭页面</button>
    </div>
</body>
</html>
        '''

    def generate_common_success_page(self, title, message):
        """生成通用的成功提示页面"""
        return f'''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/fluent.css">
</head>
<body>
    <div class="fluent-card">
        <div class="fluent-icon" style="background: #107c10;">✔</div>
        <h1 class="fluent-title">{title}</h1>
        <p class="fluent-text">{message}</p>
        <p class="fluent-text">您现在可以关闭此页面并返回启动器</p>
        <button class="fluent-btn fluent-btn-primary" onclick="window.close()">关闭页面</button>
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