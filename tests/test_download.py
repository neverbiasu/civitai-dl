import os
import sys
import time

from civitai_dl.api import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine

# 禁用所有系统代理设置
os.environ["NO_PROXY"] = "*"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 修改导入路径，使用新的API模块

# 测试通用配置
TEST_DIR = "./test_downloads"
NEGATIVE_XL_MODEL_ID = 134583  # NegativeXL模型ID
TIMEOUT = 30  # 超时时间（秒）


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"


def progress_callback(downloaded, total):
    """显示下载进度的回调函数"""
    percent = (downloaded / total) * 100
    print(
        f"\r下载进度: {percent:.1f}% ({format_size(downloaded)}/{format_size(total)})",
        end="",
    )


def test_basic_download():
    """测试直接URL下载功能（不使用API）"""
    print("\n正在测试基本下载功能...")

    # 准备下载环境
    os.makedirs(TEST_DIR, exist_ok=True)
    downloader = DownloadEngine(output_dir=TEST_DIR)

    # 测试下载URL
    test_url = f"https://civitai.com/api/download/models/{NEGATIVE_XL_MODEL_ID}"
    print(f"下载URL: {test_url}")

    # 开始下载
    task = downloader.download(test_url, progress_callback=progress_callback)

    # 监控下载进度
    print(f"文件将保存为: {task.file_path}")
    while task.status == "running":
        time.sleep(0.5)

    # 检查结果
    print(f"\n下载状态: {task.status}")
    if task.status == "completed":
        file_size = os.path.getsize(task.file_path)
        print(f"测试通过! 文件大小: {format_size(file_size)}")
        print(f"保存路径: {task.file_path}")

        # 验证文件扩展名是否正确
        _, ext = os.path.splitext(task.file_path)
        if ext in [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]:
            print(f"文件扩展名正确: {ext}")
        else:
            print(f"警告: 文件扩展名可能不正确: {ext}")
    else:
        print(f"测试失败: {task.error}")


def test_api_model_download():
    """测试通过API获取信息并下载"""
    print("\n正在测试API模型下载功能...")

    # 准备测试环境
    os.makedirs(TEST_DIR, exist_ok=True)
    api = CivitaiAPI(verify=False, proxy=None)

    try:
        # 获取模型信息
        print(f"获取模型信息 (ID: {NEGATIVE_XL_MODEL_ID})...")
        model_info = api.get_model(NEGATIVE_XL_MODEL_ID)

        # 验证模型信息
        if not model_info or isinstance(model_info, dict) and "error" in model_info:
            print(f"无法获取模型信息: {model_info.get('error', 'Unknown error')}")
            return

        print(f"模型名称: {model_info['name']}")

        # 获取最新版本和主文件
        version = model_info["modelVersions"][0]
        primary_file = next(
            (f for f in version["files"] if f.get("primary", False)),
            version["files"][0],
        )

        print(f"版本: {version['name']}")
        print(f"文件: {primary_file['name']} ({primary_file['sizeKB']} KB）")

        # 下载文件
        downloader = DownloadEngine(output_dir=TEST_DIR)

        # 使用文件的原始名称
        filename = primary_file["name"]
        if not any(filename.endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]):
            filename += ".safetensors"  # 添加默认扩展名

        file_path = os.path.join(TEST_DIR, filename)
        print(f"将下载到: {file_path}")

        # 开始下载
        task = downloader.download(
            url=primary_file["downloadUrl"],
            file_path=file_path,
            progress_callback=progress_callback,
        )

        # 监控下载状态
        while task.status == "running":
            time.sleep(0.5)

        # 检查结果
        print(f"\n下载状态: {task.status}")
        if task.status == "completed":
            print(f"测试通过! 文件已保存到: {task.file_path}")
        else:
            print(f"测试失败: {task.error}")

    except Exception as e:
        print(f"测试过程中出错: {str(e)}")


if __name__ == "__main__":
    # 选择要运行的测试
    test_basic_download()  # 测试直接URL下载
    # test_api_model_download()  # 测试通过API下载
