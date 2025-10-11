import json

'''
修改 config.json 文件中的指定字段
'''
# 读取 config.json 文件
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

# 修改 config.json 的指定字段
config['first-run'] = True
config['size'] = 85
config['repeat_run'] = False
config['show_runtime_do'] = True
config['Customize'] = []
config['Bloret_PassPort_Login'] = False
config['Bloret_PassPort_UserName'] = ""
config['Bloret_PassPort_PassWord'] = ""
config['Bloret_PassPort_Admin'] = False
config['whenCWopen_BLopen'] = True
config['home_show_login_mod'] = True
config['localmod'] = False
config['MaxThread'] = 64
config['minecraft_dir'] = ""

# 保存修改后的 config.json
with open('config.json', 'w', encoding='utf-8') as config_file:
    json.dump(config, config_file, indent=4)

print("Config values updated successfully.")

'''
修改 cmcl.json 文件中的指定字段
'''
# 读取 cmcl.json 文件
with open('cmcl.json', 'r', encoding='utf-8') as cmcl_file:
    cmcl = json.load(cmcl_file)

# 修改 cmcl.json 的指定字段
cmcl['language-run'] = "zh"
cmcl['downloadSource'] = 1
cmcl['checkAccountBeforeStart'] = False
cmcl['accounts'] = []
cmcl['printStartupInfo'] = True

# 保存修改后的 cmcl.json
with open('cmcl.json', 'w', encoding='utf-8') as cmcl_file:
    json.dump(cmcl, cmcl_file, indent=4)

print("CMCL values updated successfully.")

'''
修改 Bloret-Launcher-Setup.iss 文件中的 MyAppVersion 字段
'''
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
        setup_content[i] = f'#define MyAppVersion "{version_str}-Beta"\n'
        break

# 保存修改后的内容
with open(setup_file_path, 'w', encoding='utf-8') as setup_file:
    setup_file.writelines(setup_content)

print(f"Updated MyAppVersion to {version_str} in {setup_file_path}")