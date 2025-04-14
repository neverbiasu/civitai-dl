"""环境变量处理工具"""
import os
import re


def load_env_file(env_file=None):
    """
    从.env文件加载环境变量

    Args:
        env_file: .env文件路径，如果为None，则尝试在项目根目录查找
    """
    if env_file is None:
        # 尝试找到项目根目录
        current_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        env_file = os.path.join(current_dir, ".env")

    # 如果.env文件存在，加载它
    if os.path.isfile(env_file):
        print(f"从 {env_file} 加载环境变量")
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                match = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line)
                if match:
                    key, value = match.groups()
                    if key not in os.environ:  # 不覆盖已存在的环境变量
                        os.environ[key] = value
                        print(f"设置环境变量: {key}={value}")
