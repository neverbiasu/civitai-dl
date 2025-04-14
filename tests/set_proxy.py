"""
用于设置和验证代理的工具脚本
"""
import argparse
import os
import sys

import requests


def test_proxy(proxy=None):
    """测试代理连接"""
    proxy = proxy or os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    if not proxy:
        print("错误: 未设置代理。请提供代理地址或设置环境变量。")
        return False

    print(f"测试代理连接: {proxy}")
    try:
        # 使用代理连接测试网站
        response = requests.get(
            "https://api.ipify.org",
            proxies={"http": proxy, "https": proxy},
            timeout=10,
            verify=False,
        )
        print(f"代理测试成功! 通过代理的公共IP地址: {response.text}")

        # 测试连接Civitai
        print("测试连接Civitai API...")
        civitai_response = requests.get(
            "https://civitai.com/api/v1/models?limit=1",
            proxies={"http": proxy, "https": proxy},
            timeout=15,
            verify=False,
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
        return False


def set_proxy(proxy):
    """设置代理环境变量"""
    os.environ["CIVITAI_PROXY"] = proxy
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    print(f"已设置代理环境变量: {proxy}")
    return test_proxy(proxy)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="设置和测试代理连接")
    parser.add_argument("--proxy", help="代理地址，例如: http://127.0.0.1:7890")

    args = parser.parse_args()

    if args.proxy:
        success = set_proxy(args.proxy)
    else:
        success = test_proxy()

    sys.exit(0 if success else 1)
