import requests
import json
import modules.globals as BLglobals
import modules.config as cfg
from modules.log import log


def _get_base_url():
    return BLglobals.server_ip + ':21111'


def _get_session_cookie():
    """从 config.json 读取 bbbs_session，返回 cookies dict"""
    config_data = cfg.read()
    session = config_data.get('bbbs_session', '')
    if session:
        return {'session': session}
    return {}


def is_authenticated():
    config_data = cfg.read()
    return bool(config_data.get('bbbs_session', ''))


def fetch_summary():
    """GET /api/summary - 获取 AI 每日摘要"""
    url = f"{_get_base_url()}/api/summary"
    cookies = _get_session_cookie()
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[BBBS] 获取每日摘要失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log(f"[BBBS] 获取每日摘要网络错误: {e}")
        return None


def fetch_leaderboard_posts():
    """GET /api/leaderboard/posts - 获取热门帖子排行 Top 50"""
    url = f"{_get_base_url()}/api/leaderboard/posts"
    cookies = _get_session_cookie()
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[BBBS] 获取热帖排行失败，状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        log(f"[BBBS] 获取热帖排行网络错误: {e}")
        return []


def fetch_all_posts():
    """GET /api/all-posts - 获取最近 200 条帖子"""
    url = f"{_get_base_url()}/api/all-posts"
    cookies = _get_session_cookie()
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[BBBS] 获取最新帖子失败，状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        log(f"[BBBS] 获取最新帖子网络错误: {e}")
        return []
