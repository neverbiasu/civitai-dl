"""
测试Civitai API连接
简化版API连接测试，支持代理设置
"""

import os
import sys
import logging
from civitai_dl.api import CivitaiAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 设置代理环境变量 - 根据实际环境修改
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"


def test_api_connection(verify_ssl=False):
    """测试API连接，使用系统代理"""
    logger.info("开始测试 Civitai API 连接...")

    try:
        # 创建API客户端（禁用SSL验证）
        api = CivitaiAPI(verify_ssl=verify_ssl)

        # 测试获取模型列表
        logger.info("获取模型列表...")
        models = api.get_models(params={"limit": 1})

        if "items" in models and len(models["items"]) > 0:
            logger.info(f"✅ 成功获取模型列表! 返回了 {len(models['items'])} 个模型")
            model = models["items"][0]
            logger.info(f"  - 模型名称: {model['name']}")
            logger.info(f"  - 模型ID: {model['id']}")
            logger.info(f"  - 模型类型: {model['type']}")

            return True
        else:
            logger.error("未返回有效的模型数据")
            return False
    except Exception as e:
        logger.error(f"API连接测试失败: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    # 默认禁用SSL验证以解决代理SSL问题
    success = test_api_connection(verify_ssl=False)
    if success:
        logger.info("API连接测试成功!")
        sys.exit(0)
    else:
        logger.error("API连接测试失败!")
        sys.exit(1)
