import time
import requests
from typing import Dict, List, Optional, Any, Union

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

class APIError(Exception):
    """API请求错误"""
    def __init__(self, message, response=None, url=None):
        self.message = message
        self.response = response
        self.url = url
        self.status_code = response.status_code if response else None
        
        # 添加可能的解决方案
        self.solutions = self._get_solutions()
        
        # 构建包含解决方案的完整错误消息
        full_message = message
        if self.solutions:
            full_message += "\nPossible solutions:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(self.solutions)])
        
        super().__init__(full_message)
    
    def _get_solutions(self):
        """根据错误类型提供可能的解决方案"""
        solutions = []
        
        if 'Proxy' in self.message or 'proxy' in self.message:
            solutions.extend([
                "Check if the proxy server is running",
                "Verify the proxy address and port",
                "Ensure the proxy server allows access to the target site",
                "Try using a different proxy server",
                "Use --no-proxy option to disable proxy"
            ])
        elif 'timeout' in self.message.lower():
            solutions.extend([
                "Check your internet connection",
                "Try again later, the server might be busy",
                "Increase the timeout value using --timeout option"
            ])
        elif self.status_code == 401:
            solutions.extend([
                "Check your API key",
                "Ensure your API key has the necessary permissions"
            ])
        elif self.status_code == 403:
            solutions.extend([
                "You don't have permission to access this resource",
                "Check if you need to authenticate",
                "Ensure your API key is correct"
            ])
        elif self.status_code == 404:
            solutions.extend([
                "The requested resource does not exist",
                "Check the ID or endpoint URL"
            ])
        elif self.status_code and self.status_code >= 500:
            solutions.extend([
                "The server encountered an error",
                "Try again later",
                "Check Civitai status page for any outages"
            ])
        
        # 添加通用解决方案
        if not solutions:
            solutions.extend([
                "Check your internet connection",
                "Verify the API endpoint is correct",
                "Ensure you're using the latest version of the client"
            ])
        
        return solutions

class CivitaiAPI:
    """Civitai API客户端"""
    
    def __init__(self, api_key=None, base_url="https://civitai.com/api/v1", 
                 proxy=None, verify=True, timeout=30, max_retries=3, retry_delay=2):
        """
        初始化API客户端
        
        Args:
            api_key: Civitai API密钥(可选)
            base_url: API基础URL
            proxy: 代理服务器地址(可选,格式如 'http://user:pass@host:port')
            verify: 是否验证SSL证书
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试间隔时间(秒)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 设置代理
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
            logger.info(f"使用代理: {proxy}")
        
        # SSL验证设置
        if not verify:
            self.session.verify = False
            logger.warning("Warning: SSL verification is disabled, this may pose security risks")
            # 禁用 urllib3 的警告
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 设置请求头
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.session.headers.update(headers)
        
        # 请求限制配置
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 秒
    
    def _make_request(self, method, endpoint, params=None, data=None, json=None):
        """发送API请求并处理限制"""
        
        # 请求速率限制
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # 重试逻辑
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                
                # 记录请求时间
                self.last_request_time = time.time()
                
                # 检查返回状态
                response.raise_for_status()
                
                # 解析返回结果
                if response.content:
                    return response.json()
                return None
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误: {e}")
                
                # 如果是速率限制问题，等待并重试
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"API请求频率过高，等待{retry_after}秒后重试...")
                    time.sleep(retry_after)
                    retries += 1
                    last_error = e
                    continue
                
                # 其他HTTP错误直接返回
                return self._handle_error(e.response, url)
                
            except requests.exceptions.ProxyError as e:
                logger.error(f"代理服务器错误: {e}")
                # 如果是代理错误，可能不值得重试
                # 但是如果是临时性错误，可以尝试重试
                last_error = e
                if retries < self.max_retries:
                    logger.info(f"重试 ({retries+1}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                    retries += 1
                else:
                    raise APIError(f"Proxy server connection failed: {str(e)}", None, url)
                
            except (requests.exceptions.Timeout, 
                   requests.exceptions.ConnectionError) as e:
                logger.error(f"连接错误: {e}")
                last_error = e
                if retries < self.max_retries:
                    logger.info(f"重试 ({retries+1}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                    retries += 1
                else:
                    error_type = "连接超时" if isinstance(e, requests.exceptions.Timeout) else "连接错误"
                    raise APIError(f"{error_type}: {str(e)}", None, url)
                
            except Exception as e:
                logger.error(f"请求异常: {e}")
                last_error = e
                if retries < self.max_retries:
                    logger.info(f"重试 ({retries+1}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                    retries += 1
                else:
                    raise APIError(f"API请求在 {self.max_retries} 次尝试后仍失败: {str(e)}", None, url)
        
        # 达到最大重试次数后仍然失败
        if last_error:
            raise APIError(f"API请求在 {self.max_retries} 次尝试后仍失败: {str(last_error)}", None, url)
        
        return {"error": "未知错误"}
    
    def _handle_error(self, response, url):
        """处理API错误响应"""
        try:
            error_data = response.json()
        except:
            error_data = {"message": response.text}
        
        logger.error(f"API错误 ({response.status_code}): {error_data}")
        raise APIError(f"API错误 {response.status_code}: {error_data.get('message', response.text)}", response, url)
    
    def get_model(self, model_id: int) -> dict:
        """获取模型详细信息"""
        return self._make_request("GET", f"/models/{model_id}")
    
    def search_models(self, query=None, tag=None, username=None, type=None,
                     nsfw=None, sort=None, period=None, page=1, page_size=20) -> dict:
        """搜索模型"""
        params = {
            "query": query,
            "tag": tag,
            "username": username,
            "type": type,
            "nsfw": nsfw,
            "sort": sort,
            "period": period,
            "page": page,
            "pageSize": page_size
        }
        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/models", params=params)
    
    def get_model_version(self, version_id: int) -> dict:
        """获取模型特定版本的详细信息"""
        return self._make_request("GET", f"/model-versions/{version_id}")
    
    def get_images_by_model(self, model_id: int, nsfw=None, page=1, page_size=20) -> dict:
        """获取模型相关图像"""
        params = {
            "modelId": model_id,
            "nsfw": nsfw,
            "page": page,
            "pageSize": page_size
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/images", params=params)
