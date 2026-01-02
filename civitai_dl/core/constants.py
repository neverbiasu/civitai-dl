"""Constants used throughout the application."""

# Regex patterns
INVALID_FILENAME_CHARS = r'[\\/*?:"<>|]'
WORD_CHAR_CLASS = r'\w'
NON_QUOTE_CHARS = r'[^\"]+'

# UI Strings
PROMPT_PLACEHOLDER = "请输入有效的模型ID"
DOWNLOAD_DIR_DEFAULT = "./downloads"
HTTP_PREFIX = "http://"
UTF8_ENCODING = "UTF-8"

# API/Stats fields
STATS_RATING = "stats.rating"
STATS_DOWNLOAD_COUNT = "stats.downloadCount"
