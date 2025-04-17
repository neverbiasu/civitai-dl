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

## Changelog

### v0.1.1 (2023-11-22)

- **Feature**: Added `browse` command group to search and explore models from the CLI
- **Feature**: Implemented advanced filter builder component for both WebUI and CLI searches
- **Feature**: Added filter templates to save and reuse complex search conditions

### v0.1.0 (2023-11-15)

- Initial release
- Support downloading model files by model ID
- Support downloading specific version files by model ID and version ID
- Support downloading associated example images for models
- Provided basic Command Line Interface (CLI)
- Provided experimental Web User Interface (WebUI)
- Support for proxy settings
- Support for API key authentication

## Contributing

Pull requests and issue reports are welcome.

## License

MIT License
