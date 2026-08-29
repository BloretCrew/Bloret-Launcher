import requests
import modules.globals as BLglobals


def log(message, level=None):
    try:
        from modules.log import log as app_log
        return app_log(message, level) if level is not None else app_log(message)
    except ImportError:
        import logging
        logging.getLogger(__name__).log(level or logging.INFO, message)


def _read_config():
    try:
        import modules.config as cfg
        return cfg.read()
    except ImportError:
        return {}


def _get_base_url():
    return BLglobals.server_ip + ':21111'


def _get_session_cookie():
    """从 config.json 读取 bbbs_session，返回 cookies dict"""
    config_data = _read_config()
    session = config_data.get('bbbs_session', '')
    if session:
        return {'session': session}
    return {}


def _get_json(url, failure_message, default, expected_type):
    cookies = _get_session_cookie()
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        if response.status_code != 200:
            log(f"[BBBS] {failure_message}，状态码: {response.status_code}")
            return default
        try:
            payload = response.json()
        except (ValueError, TypeError) as e:
            log(f"[BBBS] {failure_message}，响应 JSON 解析失败: {e}")
            return default
        if not isinstance(payload, expected_type):
            log(f"[BBBS] {failure_message}，响应数据类型异常: {type(payload).__name__}")
            return default
        return payload
    except requests.exceptions.RequestException as e:
        log(f"[BBBS] {failure_message}，网络错误: {e}")
        return default


def is_authenticated():
    config_data = _read_config()
    return bool(config_data.get('bbbs_session', ''))


def fetch_summary():
    """GET /api/summary - 获取 AI 每日摘要"""
    return _get_json(
        f"{_get_base_url()}/api/summary",
        "获取每日摘要失败",
        None,
        dict,
    )


def fetch_leaderboard_posts():
    """GET /api/leaderboard/posts - 获取热门帖子排行 Top 50"""
    return _get_json(
        f"{_get_base_url()}/api/leaderboard/posts",
        "获取热帖排行失败",
        [],
        list,
    )


def fetch_all_posts():
    """GET /api/all-posts - 获取最近 200 条帖子"""
    return _get_json(
        f"{_get_base_url()}/api/all-posts",
        "获取最新帖子失败",
        [],
        list,
    )
