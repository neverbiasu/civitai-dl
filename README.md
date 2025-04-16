# Civitai-DL

[![PyPI - Version](https://img.shields.io/pypi/v/civitai-dl.svg)](https://pypi.org/project/civitai-dl/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/civitai-dl.svg)](https://pypi.org/project/civitai-dl/)
[![GitHub License](https://img.shields.io/github/license/neverbiasu/civitai-dl.svg)](https://github.com/neverbiasu/civitai-dl/blob/main/LICENSE)

A tool designed for AI art creators to efficiently browse, download, and manage model resources from the Civitai platform.

[中文文档](README_CN.md) | English

## Features

- Model search and browsing
- Batch download of models and images
- Resume downloads and queue management
- Both graphical interface and command line interaction

## Installation

### Using pip

```bash
pip install civitai-dl
```

### From source

```bash
# Clone repository
git clone https://github.com/neverbiasu/civitai-dl.git
cd civitai-dl

# Install using Poetry
poetry install
```

## Quick Start

### Command Line Usage

```bash
# Download model by ID
civitai-dl download model 12345

# Search models
civitai-dl browse models --query "portrait" --type "LORA"
```

### Launch Web Interface

```bash
civitai-dl webui
```

## Documentation

For detailed documentation, please visit [project documentation site](https://github.com/neverbiasu/civitai-dl).

## Contributing

Pull requests and issue reports are welcome.

## License

MIT License
