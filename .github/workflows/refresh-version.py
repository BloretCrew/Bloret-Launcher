import json
import subprocess

# 读取 config.json 文件
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

# 获取 ver 值并转换为字符串
version = config.get('ver', '')
version_str = str(version)

# 读取 Bloret-Launcher-Setup.iss 文件
setup_file_path = 'Bloret-Launcher-Setup.iss'
with open(setup_file_path, 'r', encoding='utf-8') as setup_file:
    setup_content = setup_file.readlines()

# 修改 MyAppVersion 的值
for i, line in enumerate(setup_content):
    if line.startswith('#define MyAppVersion'):
        setup_content[i] = f'#define MyAppVersion "{version_str}"'
        break

# 保存修改后的内容
with open(setup_file_path, 'w', encoding='utf-8') as setup_file:
    setup_file.writelines(setup_content)

# 提交更改到 Git
subprocess.run(['git', 'add', setup_file_path], check=True)
subprocess.run(['git', 'commit', '-m', f'更新 MyAppVersion 为 {version_str}'], check=True)
subprocess.run(['git', 'push'], check=True)

print(f"Updated MyAppVersion to {version_str} in {setup_file_path}")