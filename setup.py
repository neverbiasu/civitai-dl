from setuptools import setup, find_packages

setup(
    name="civitai-downloader",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "click",
        "gradio",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "civitai-dl=civitai_downloader.cli.main:main",
        ],
    },
    python_requires=">=3.8",
    author="Civitai Downloader Team",
    author_email="example@example.com",
    description="A tool for browsing and downloading resources from Civitai",
    keywords="civitai, ai, download, stable-diffusion",
    project_urls={
        "Documentation": "https://github.com/neverbiasu/civitai-downloader",
        "Source": "https://github.com/neverbiasu/civitai-downloader",
    },
)
