import requests
import json
import sys
from urllib.parse import urlencode

def get_project_versions(project_id, loaders=None, game_versions=None, featured=None):
    """
    获取Modrinth项目版本信息
    
    Args:
        project_id (str): 项目ID或slug
        loaders (list): 加载器类型列表，如['fabric']
        game_versions (list): 游戏版本列表，如['1.18.1']
        featured (bool): 是否仅获取精选版本
    
    Returns:
        dict: API响应数据
    """
    # 构建基础URL
    url = f"https://api.modrinth.com/v2/project/{project_id}/version"
    
    # 构建查询参数
    params = {}
    if loaders:
        params['loaders'] = json.dumps(loaders)
    if game_versions:
        params['game_versions'] = json.dumps(game_versions)
    if featured is not None:
        params['featured'] = str(featured).lower()
    
    # 添加查询参数到URL
    if params:
        url += '?' + urlencode(params)
    
    try:
        # 发送GET请求
        response = requests.get(url)
        response.raise_for_status()  # 如果响应状态码不是200会抛出异常
        
        # 解析JSON响应
        data = response.json()
        
        # 保存到get.json文件
        with open('get.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"成功获取项目 {project_id} 的版本信息，已保存到 get.json")
        return data
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        loaders = sys.argv[2].split(',') if len(sys.argv) > 2 else None
        game_versions = sys.argv[3].split(',') if len(sys.argv) > 3 else None
        featured = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else None
        
        get_project_versions(project_id, loaders, game_versions, featured)
    else:
        print("用法: python GET.py <project_id> [loaders] [game_versions] [featured]")
        print("示例: python GET.py AABBCCDD fabric 1.18.1 true")
        print("示例: python GET.py my_project")