"""Main entry point for the Civitai Downloader package.

Allows running the application directly with `python -m civitai_dl`.
"""

import sys
from civitai_dl.cli.main import main


if __name__ == "__main__":
    sys.exit(main())
