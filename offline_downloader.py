import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class SimpleDownloader:
    def __init__(self, base_folder="."):
        self.base_folder = Path(base_folder)
        self.fonts_folder = self.base_folder / "fonts"
        self.images_folder = self.base_folder / "images"
        
        self.fonts_folder.mkdir(exist_ok=True)
        self.images_folder.mkdir(exist_ok=True)
        
        self.downloaded = {}
    
    def download_file(self, url, save_path):
        """Download file from URL"""
        if url in self.downloaded:
            return self.downloaded[url]
        
        try:
            print(f"  Downloading: {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(response.content)
            
            self.downloaded[url] = str(save_path)
            print(f"  ✓ Saved: {save_path.name}")
            return str(save_path)
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return None
    
    def download_google_font(self, font_url):
        """Download Google Font and return @font-face CSS"""
        try:
            print(f"\nFetching Google Font: {font_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(font_url, headers=headers)
            css_content = response.text
            
            # Find all font file URLs (woff2, woff, ttf, etc.)
            # Pattern matches: url(https://fonts.gstatic.com/...any-font-file)
            font_pattern = r'url\((https://fonts\.gstatic\.com/[^)]+\.(woff2?|ttf|otf|eot))\)'
            font_urls = re.findall(font_pattern, css_content)
            
            # Download each font file
            for font_url_match in font_urls:
                # font_url_match is a tuple (url, extension), we want just the url
                actual_url = font_url_match[0] if isinstance(font_url_match, tuple) else font_url_match
                filename = os.path.basename(urlparse(actual_url).path)
                local_path = self.fonts_folder / filename
                self.download_file(actual_url, local_path)
                
                # Replace URL with local path
                css_content = css_content.replace(actual_url, f"fonts/{filename}")
            
            return css_content
        except Exception as e:
            print(f"  ✗ Failed to fetch Google Font: {e}")
            return ""
    
    def process_html(self, html_file):
        """Process HTML file"""
        print(f"\n{'='*60}")
        print(f"Processing: {html_file}")
        print(f"{'='*60}")
        
        html_path = self.base_folder / html_file
        
        if not html_path.exists():
            print(f"✗ File not found!")
            return
        
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        modified = False
        
        # Collect all Google Font URLs
        google_font_urls = []
        
        # From <link> tags
        for link in soup.find_all('link'):
            href = link.get('href', '')
            if 'fonts.googleapis.com/css' in href:
                # Make full URL
                if not href.startswith('http'):
                    href = 'https:' + href if href.startswith('//') else 'https://' + href
                google_font_urls.append(href)
                link.decompose()
                modified = True
        
        # Remove preconnect links
        for link in soup.find_all('link', rel='preconnect'):
            href = link.get('href', '')
            if 'fonts.g' in href:
                link.decompose()
                modified = True
        
        # From @import in <style> tags
        for style in soup.find_all('style'):
            if style.string:
                imports = re.findall(r'@import\s+url\(["\']?(https://fonts\.googleapis\.com/css[^"\')\s]+)["\']?\)', style.string)
                if imports:
                    google_font_urls.extend(imports)
                    # Remove the @import lines
                    new_content = re.sub(r'@import\s+url\(["\']?https://fonts\.googleapis\.com/css[^"\')\s]+["\']?\);?', '', style.string)
                    style.string = new_content
                    modified = True
        
        # Download all Google Fonts and create new style tag
        if google_font_urls:
            all_font_css = ""
            for font_url in google_font_urls:
                font_css = self.download_google_font(font_url)
                all_font_css += font_css + "\n\n"
            
            if all_font_css.strip():
                # Add new style tag with fonts at the beginning of head
                new_style = soup.new_tag('style')
                new_style.string = all_font_css
                soup.head.insert(0, new_style)
        
        # Download external images (only if they're HTTP URLs)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('http://') or src.startswith('https://'):
                filename = os.path.basename(urlparse(src).path)
                if not filename:
                    filename = 'image.jpg'
                
                local_path = self.images_folder / filename
                downloaded = self.download_file(src, local_path)
                
                if downloaded:
                    img['src'] = f"images/{filename}"
                    modified = True
        
        # Save if modified
        if modified:
            # Backup original
            backup = html_path.with_suffix('.html.bak')
            if not backup.exists():
                html_path.rename(backup)
                print(f"\n✓ Backup created: {backup.name}")
            
            # Save modified
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            print(f"✓ Updated: {html_file}")
        else:
            print(f"→ No changes needed")


def main():
    print("=" * 60)
    print("SIMPLE OFFLINE DOWNLOADER")
    print("=" * 60)
    
    folder = input("\nEnter folder path (press Enter for current dir): ").strip()
    if not folder:
        folder = "."
    
    folder = Path(folder)
    
    if not folder.exists():
        print(f"\n✗ Folder not found: {folder}")
        return
    
    # Find HTML files
    html_files = list(folder.glob('*.html'))
    
    if not html_files:
        print(f"\n✗ No HTML files found in {folder}")
        return
    
    print(f"\nFound {len(html_files)} HTML files:")
    for i, f in enumerate(html_files, 1):
        print(f"  {i}. {f.name}")
    
    confirm = input("\nProcess these? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    downloader = SimpleDownloader(folder)
    
    for html_file in html_files:
        downloader.process_html(html_file.name)
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print("\nFolders created:")
    print("  ./fonts/  - Font files (.woff2)")
    print("  ./images/ - Images")
    print("\nBackups: .html.bak files")


if __name__ == "__main__":
    main()
