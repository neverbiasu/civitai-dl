"""
测试Civitai API连接
简化版API连接测试，支持代理设置
"""

import logging
import os
import sys

import pytest

from civitai_dl.api import CivitaiAPI

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_api_connection():
    """测试API连接，使用系统代理"""
    logger.info("开始测试 Civitai API 连接...")

    # 获取代理设置
    proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    # 如果没有代理设置，跳过测试
    if not proxy:
        pytest.skip("未设置代理，跳过测试")
        return

    logger.info(f"使用代理: {proxy}")

    try:
        # 创建API客户端（禁用SSL验证）
        api = CivitaiAPI(proxy=proxy, verify=False)

        # 测试获取模型列表
        logger.info("获取模型列表...")
        models = api.get_models(params={"limit": 1})

        if "items" in models and len(models["items"]) > 0:
            logger.info(f"✅ 成功获取模型列表! 返回了 {len(models['items'])} 个模型")
            model = models["items"][0]
            logger.info(f"  - 模型名称: {model['name']}")
            logger.info(f"  - 模型ID: {model['id']}")
            logger.info(f"  - 模型类型: {model['type']}")

            assert True, "API连接成功"
        else:
            logger.error("未返回有效的模型数据")
            assert False, "API未返回有效的模型数据"
    except Exception as e:
        logger.error(f"API连接测试失败: {type(e).__name__}: {str(e)}")
        assert False, f"API连接测试失败: {str(e)}"


if __name__ == "__main__":
    # 这里可以手动设置代理环境变量
    if not (os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")):
        os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
        os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

    try:
        test_api_connection()
        print("API连接测试成功!")
        sys.exit(0)
    except Exception as e:
        print(f"API连接测试失败: {e}")
        sys.exit(1)
