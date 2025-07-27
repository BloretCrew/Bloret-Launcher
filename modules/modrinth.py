import requests, logging
from modules.log import log

def search_mods(search_term):

    url = f"https://api.modrinth.com/v2/search?query={search_term}&limit=10"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            log(f"搜索 Modrinth 模组: {search_term} 成功", logging.INFO)
            return data
        else:
            log(f"搜索失败: {response.status_code}", logging.ERROR)
            return []
    except Exception as e:
        log(f"搜索异常: {str(e)}", logging.ERROR)
        return []