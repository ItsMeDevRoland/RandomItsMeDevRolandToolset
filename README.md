------------------------------------------------------------------
# Offline HTML Downloader

Downloads Google Fonts and external images to make HTML files work offline.

## Requirements
```bash
pip install requests beautifulsoup4
```

## Usage
```bash
python offline_downloader.py
```

Enter the folder path when prompted (or press Enter for current directory).

## What it does
- Downloads Google Fonts (.ttf files) to `fonts/` folder
- Downloads external images to `images/` folder
- Replaces URLs with local paths
- Creates .bak backups of original files
- Leaves local files (CSS, other HTMLs) untouched

## Example
```bash
$ python offline_downloader.py
Enter folder path: /path/to/website
Process these? (y/n): y
```
----------------------------------------------------------------
