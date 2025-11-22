#!/usr/bin/env python3
"""
Bloriko AI API 测试脚本
用于测试和调试AI接口的认证和功能
"""

import requests
import json
import logging
import time

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_ai_api():
    """测试AI API接口"""
    
    # API配置
    base_url = "http://pcfs.eno.ink:20000"
    api_endpoint = f"{base_url}/api/ai"
    
    # 测试不同的认证配置
    test_configs = [
        {
            "name": "文档示例配置",
            "OauthApp": {
                "app_id": "BloretLauncher",
                "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
            },
            "user": {
                "name": "Detritalw",
                "token": "1f7279b543d13f927dd053e6b6196448"
            }
        },
        {
            "name": "当前配置文件",
            "OauthApp": {
                "app_id": "BloretLauncher",
                "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
            },
            "user": {
                "name": "Detritalw",
                "token": "1f7279b543d13f927dd053e6b6196448"
            }
        }
    ]
    
    # 测试问题
    test_questions = [
        "你好",
        "黑曜石是什么",
        "Minecraft是什么游戏"
    ]
    
    for config in test_configs:
        log.info(f"\n{'='*60}")
        log.info(f"测试配置: {config['name']}")
        log.info(f"用户: {config['user']['name']}")
        log.info(f"Token: {config['user']['token']}")
        log.info(f"应用密钥: {config['OauthApp']['app_secret']}")
        
        for question in test_questions:
            log.info(f"\n--- 测试问题: {question} ---")
            
            # 构建请求数据
            payload = {
                "pause": True,  # 使用pause模式来测试继续获取功能
                "model": "Bloriko",
                "OauthApp": config["OauthApp"],
                "user": config["user"],
                "context": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            try:
                log.info(f"发送请求到: {api_endpoint}")
                log.debug(f"请求payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                
                response = requests.post(api_endpoint, json=payload, headers=headers, timeout=30)
                
                log.info(f"响应状态码: {response.status_code}")
                log.debug(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    log.info(f"响应成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    # 如果返回了pause=true，测试继续获取接口
                    if result.get("pause") and result.get("connectionId"):
                        connection_id = result["connectionId"]
                        log.info(f"检测到需要继续获取，连接ID: {connection_id}")
                        test_continue_api(connection_id, config)
                        
                elif response.status_code == 403:
                    log.error(f"403 Forbidden - 认证失败")
                    log.error(f"响应内容: {response.text}")
                    
                    # 尝试获取更详细的错误信息
                    try:
                        error_data = response.json()
                        log.error(f"错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                    except:
                        log.error(f"原始响应: {response.text}")
                        
                elif response.status_code == 400:
                    log.error(f"400 Bad Request - 请求参数错误")
                    log.error(f"响应内容: {response.text}")
                else:
                    log.error(f"意外状态码: {response.status_code}")
                    log.error(f"响应内容: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                log.error(f"请求异常: {type(e).__name__}: {str(e)}")
            except json.JSONDecodeError as e:
                log.error(f"JSON解析失败: {str(e)}")
                log.error(f"原始响应: {response.text}")
            except Exception as e:
                log.error(f"未知错误: {type(e).__name__}: {str(e)}")
                
            # 短暂延迟避免频繁请求
            time.sleep(1)

def test_continue_api(connection_id, config):
    """测试继续获取API接口"""
    
    base_url = "http://pcfs.eno.ink:20000"
    
    log.info(f"\n测试继续获取接口，连接ID: {connection_id}")
    
    # 只测试标准的继续获取接口
    endpoint = f"{base_url}/api/ai-continue"
    log.info(f"\n--- 测试继续接口: {endpoint} (方法: POST) ---")
    
    payload = {
        "connectionId": connection_id
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    log.info(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
    log.info(f"请求头: {headers}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        log.info(f"响应状态码: {response.status_code}")
        log.info(f"响应头: {dict(response.headers)}")
        log.info(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            log.info(f"响应成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 如果获取到了内容，返回成功
            if result.get("content"):
                log.info(f"✅ 成功获取到AI回复: {result['content']}")
                return result["content"]
            elif result.get("message") == "AI正在处理中，请稍后重试":
                log.info("⏳ AI还在处理中，等待2秒后重试...")
                time.sleep(2)
                return test_continue_endpoint(connection_id, config)  # 递归重试
                
        elif response.status_code == 404:
            log.error(f"❌ 404 Not Found - 接口不存在: {endpoint}")
            log.error(f"这可能意味着服务器端没有正确注册这个路由")
            
        elif response.status_code == 403:
            log.error(f"❌ 403 Forbidden - 认证失败")
            log.error(f"可能需要检查token或其他认证信息")
            
        elif response.status_code == 400:
            log.error(f"❌ 400 Bad Request - 请求参数错误")
            log.error(f"可能需要检查请求参数格式")
            
        else:
            log.error(f"❌ 意外状态码: {response.status_code}")
            log.error(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        log.error(f"❌ 请求异常: {type(e).__name__}: {str(e)}")
    except json.JSONDecodeError as e:
        log.error(f"❌ JSON解析失败: {str(e)}")
        log.error(f"原始响应: {response.text}")
    except Exception as e:
        log.error(f"❌ 未知错误: {type(e).__name__}: {str(e)}")
    
    return None  # 测试失败
    
    payload = {
        "connectionId": connection_id
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
             
        log.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log.info(f"响应成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 如果获取到了内容，返回成功
            if result.get("content"):
                log.info(f"成功获取到AI回复: {result['content']}")
                return result["content"]
            elif result.get("message") == "AI正在处理中，请稍后重试":
                log.info("AI还在处理中，等待2秒后重试...")
                time.sleep(2)
                return test_continue_endpoint(connection_id, config)  # 递归重试
                
        elif response.status_code == 404:
            log.warning(f"404 Not Found - 接口不存在")
            # 尝试GET方式作为备选
            log.info("尝试GET方式作为备选...")
            get_endpoint = f"{base_url}/api/ai-continue?connectionId={connection_id}"
            try:
                get_response = requests.get(get_endpoint, timeout=30)
                log.info(f"GET方式响应状态码: {get_response.status_code}")
                if get_response.status_code == 200:
                    get_result = get_response.json()
                    log.info(f"GET方式响应成功: {json.dumps(get_result, ensure_ascii=False, indent=2)}")
                    if get_result.get("content"):
                        log.info(f"GET方式成功获取到AI回复: {get_result['content']}")
                        return get_result["content"]
            except Exception as get_e:
                log.error(f"GET方式也失败了: {get_e}")
        else:
            log.error(f"意外状态码: {response.status_code}")
            log.error(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        log.error(f"请求异常: {type(e).__name__}: {str(e)}")
    except json.JSONDecodeError as e:
        log.error(f"JSON解析失败: {str(e)}")
        log.error(f"原始响应: {response.text}")
    except Exception as e:
        log.error(f"未知错误: {type(e).__name__}: {str(e)}")
    
    return None  # 返回None表示失败

def test_without_authentication():
    """测试无认证访问"""
    
    base_url = "http://pcfs.eno.ink:20000"
    endpoints = [
        f"{base_url}/api/ai",
        f"{base_url}/api/ai-continue",
        f"{base_url}/health" if False else None  # 如果有健康检查接口
    ]
    
    log.info(f"\n{'='*60}")
    log.info("测试无认证访问")
    
    for endpoint in endpoints:
        if not endpoint:
            continue
            
        log.info(f"\n--- 测试无认证访问: {endpoint} ---")
        
        try:
            response = requests.get(endpoint, timeout=10)
            log.info(f"响应状态码: {response.status_code}")
            log.info(f"响应内容: {response.text[:200]}...")  # 只显示前200字符
            
        except requests.exceptions.RequestException as e:
            log.error(f"请求异常: {type(e).__name__}: {str(e)}")
        except Exception as e:
            log.error(f"未知错误: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    log.info("开始测试 Bloriko AI API")
    log.info(f"API基础地址: http://pcfs.eno.ink:20000")
    
    # 1. 先测试无认证访问
    test_without_authentication()
    
    # 2. 测试有认证访问
    test_ai_api()
    
    log.info("\n测试完成!")