"""
用于设置和验证代理的工具脚本
"""
import os
import sys
import requests
import subprocess
import argparse
from urllib.parse import urlparse

def detect_system_proxy():
    """
    尝试自动检测系统代理设置
    """
    # 从系统环境变量中获取
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    
    if proxy:
        print(f"已检测到系统代理设置: {proxy}")
        return proxy
        
    # 在Windows上尝试获取IE代理设置
    if sys.platform == 'win32':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as key:
                proxy_enable, _ = winreg.QueryValueEx(key, 'ProxyEnable')
                if proxy_enable:
                    proxy_server, _ = winreg.QueryValueEx(key, 'ProxyServer')
                    if proxy_server:
                        # 确保格式正确
                        if not proxy_server.startswith('http://'):
                            proxy_server = f'http://{proxy_server}'
                        print(f"检测到Windows IE代理设置: {proxy_server}")
                        return proxy_server
        except Exception as e:
            print(f"尝试检测Windows代理时出错: {str(e)}")
    
    # 尝试从工具中获取代理信息
    proxy_tools = {
        'clash': ['clash-meta.exe', 'clash.exe', 'clash'],
        'v2ray': ['v2ray.exe', 'v2ray'],
        'shadowsocks': ['ss-local.exe', 'ss-local']
    }
    
    for tool_name, execs in proxy_tools.items():
        for exec_name in execs:
            if find_executable(exec_name):
                print(f"检测到{tool_name}代理工具，可能在使用默认端口")
                
                # 对于不同的工具，尝试不同的默认端口和协议
                if tool_name == 'clash':
                    return "http://127.0.0.1:7890"
                elif tool_name == 'v2ray':
                    return "socks5://127.0.0.1:1080"
                elif tool_name == 'shadowsocks':
                    return "socks5://127.0.0.1:1080"
    
    return None

def find_executable(name):
    """查找可执行文件"""
    if sys.platform == "win32":
        cmd = f"where {name}"
    else:
        cmd = f"which {name}"
    
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def test_proxy(proxy=None):
    """测试代理连接"""
    proxy = proxy or os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    
    if not proxy:
        print("错误: 未设置代理。请提供代理地址或设置环境变量。")
        return False
    
    print(f"测试代理连接: {proxy}")
    
    # 保存环境变量的原始值
    original_http_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    
    # 临时设置环境变量
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    
    try:
        # 尝试不同的代理协议
        proxies = {"http": proxy, "https": proxy}
        
        # 使用代理连接测试网站
        print("测试连接到 api.ipify.org...")
        response = requests.get(
            "https://api.ipify.org",
            proxies=proxies,
            timeout=10,
            verify=False
        )
        print(f"代理测试成功! 通过代理的公共IP地址: {response.text}")
        
        # 测试连接Civitai
        print("测试连接Civitai API...")
        civitai_response = requests.get(
            "https://civitai.com/api/v1/models?limit=1",
            proxies=proxies,
            timeout=15,
            verify=False
        )
        if civitai_response.status_code == 200:
            print(f"成功连接Civitai API! 状态码: {civitai_response.status_code}")
            model_data = civitai_response.json()
            if "items" in model_data and len(model_data["items"]) > 0:
                model = model_data["items"][0]
                print(f"  - 获取到模型: {model['name']} (ID: {model['id']})")
            return True
        else:
            print(f"连接Civitai API失败! 状态码: {civitai_response.status_code}")
            return False
    except Exception as e:
        print(f"代理测试失败: {type(e).__name__}: {str(e)}")
        
        # 如果是HTTP代理失败，尝试SOCKS代理
        try:
            if "http://" in proxy:
                socks_proxy = proxy.replace("http://", "socks5://")
                print(f"尝试将HTTP代理转换为SOCKS5代理: {socks_proxy}")
                
                socks_proxies = {"http": socks_proxy, "https": socks_proxy}
                response = requests.get(
                    "https://api.ipify.org",
                    proxies=socks_proxies,
                    timeout=10,
                    verify=False
                )
                print(f"SOCKS5代理测试成功! 通过代理的公共IP地址: {response.text}")
                return socks_proxy
        except Exception as e:
            print(f"SOCKS5代理测试也失败: {str(e)}")
        
        return False
    finally:
        # 恢复环境变量
        if original_http_proxy:
            os.environ["HTTP_PROXY"] = original_http_proxy
        elif "HTTP_PROXY" in os.environ:
            del os.environ["HTTP_PROXY"]
            
        if original_https_proxy:
            os.environ["HTTPS_PROXY"] = original_https_proxy
        elif "HTTPS_PROXY" in os.environ:
            del os.environ["HTTPS_PROXY"]

def set_proxy(proxy_url):
    """设置代理环境变量"""
    if not proxy_url:
        print("错误: 提供的代理地址为空")
        return False
    
    # 解析代理URL
    try:
        parsed = urlparse(proxy_url)
        if not parsed.scheme:
            # 如果没有协议，默认添加http://
            proxy_url = f"http://{proxy_url}"
            print(f"添加默认http://协议: {proxy_url}")
    except Exception as e:
        print(f"代理URL格式错误: {str(e)}")
        return False
    
    # 测试代理是否可用
    successful_proxy = test_proxy(proxy_url)
    
    if successful_proxy:
        # 如果是字符串，表示测试成功，可能是转换后的代理地址
        if isinstance(successful_proxy, str):
            proxy_url = successful_proxy
            
        print(f"设置环境变量 CIVITAI_PROXY={proxy_url}")
        os.environ["CIVITAI_PROXY"] = proxy_url
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        
        # 创建.env文件保存设置
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"CIVITAI_PROXY={proxy_url}\n")
            f.write(f"HTTP_PROXY={proxy_url}\n")
            f.write(f"HTTPS_PROXY={proxy_url}\n")
        print(f"代理配置已保存到 {env_file}")
        
        return True
    else:
        print("代理设置失败，无法连接到测试网站")
        return False

def main():
    parser = argparse.ArgumentParser(description="设置和测试代理连接")
    parser.add_argument("--proxy", help="代理地址，例如: http://127.0.0.1:7890")
    parser.add_argument("--detect", action="store_true", help="尝试自动检测系统代理设置")
    parser.add_argument("--test", action="store_true", help="只测试现有代理，不设置")
    
    args = parser.parse_args()
    
    if args.detect:
        proxy = detect_system_proxy()
        if proxy:
            print(f"已检测到代理: {proxy}")
            if not args.test:
                success = set_proxy(proxy)
                return 0 if success else 1
        else:
            print("无法自动检测代理设置")
            return 1
    elif args.proxy:
        if args.test:
            success = test_proxy(args.proxy)
        else:
            success = set_proxy(args.proxy)
        return 0 if success else 1
    elif args.test:
        success = test_proxy()
        return 0 if success else 1
    else:
        parser.print_help()
        return 1
        
if __name__ == "__main__":
    sys.exit(main())
