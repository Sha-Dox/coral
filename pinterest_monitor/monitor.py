import re
import requests
import time
from urllib.parse import urljoin, urlparse
from config import config

class PinterestMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('scraping', 'user_agent')
        })
        self.request_delay = config.get_float('scraping', 'request_delay')
    
    def get_pin_count(self, board_url):
        """Extract pin count from a Pinterest board URL"""
        try:
            response = self.session.get(board_url, timeout=10)
            response.raise_for_status()
            
            # Use regex to find pin_count in the HTML
            match = re.search(r'"pin_count":(\d+)', response.text)
            if match:
                return int(match.group(1))
            
            return None
        except Exception as e:
            print(f"Error fetching pin count for {board_url}: {e}")
            return None
    
    def get_user_boards(self, username):
        """Get all boards for a Pinterest user"""
        boards = []
        
        # Try different Pinterest domains
        domains = ['www.pinterest.com', 'tr.pinterest.com', 'pinterest.com']
        
        for domain in domains:
            user_url = f"https://{domain}/{username}/"
            
            try:
                response = self.session.get(user_url, timeout=10)
                response.raise_for_status()
                
                # Find all board links in the HTML
                # Pattern: "/username/board-name/"
                pattern = rf'"(/{username}/[^"/]+/)"'
                matches = re.findall(pattern, response.text)
                
                if matches:
                    # Remove duplicates and filter out special pages
                    unique_boards = set(matches)
                    excluded = {'_created', '_saved', '_pins', 'pins', 'boards'}
                    
                    for board_path in unique_boards:
                        # Extract board slug
                        board_slug = board_path.strip('/').split('/')[-1]
                        
                        if board_slug not in excluded and not board_slug.startswith('_'):
                            board_url = f"https://{domain}{board_path}"
                            
                            # Try to get board name and pin count
                            board_info = self.get_board_info(board_url)
                            if board_info:
                                boards.append(board_info)
                            
                            # Small delay to be respectful
                            time.sleep(self.request_delay)
                    
                    if boards:
                        return boards
            
            except Exception as e:
                print(f"Error fetching boards from {domain} for user {username}: {e}")
                continue
        
        return boards
    
    def get_board_info(self, board_url):
        """Get detailed information about a board"""
        try:
            response = self.session.get(board_url, timeout=10)
            response.raise_for_status()
            
            # Extract pin count
            pin_count_match = re.search(r'"pin_count":(\d+)', response.text)
            pin_count = int(pin_count_match.group(1)) if pin_count_match else 0
            
            # Extract board name - try multiple patterns in order of preference
            board_name = None
            
            # 1. Try to get from board-specific JSON
            board_json_match = re.search(r'"board"[^}]*"name":"([^"]+)"', response.text)
            if board_json_match:
                board_name = board_json_match.group(1)
            
            # 2. Try og:title meta tag
            if not board_name:
                og_title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
                if og_title_match:
                    board_name = og_title_match.group(1)
            
            # 3. Fallback to URL extraction
            if not board_name:
                board_name = self._extract_name_from_url(board_url)
            
            # Clean up the name
            board_name = board_name.replace('\\u002F', '/').replace('\\', '')
            
            # Extract username
            username_match = re.search(r'"username":"([^"]+)"', response.text)
            username = username_match.group(1) if username_match else self._extract_username_from_url(board_url)
            
            return {
                'url': board_url,
                'name': board_name,
                'username': username,
                'pin_count': pin_count
            }
        
        except Exception as e:
            print(f"Error fetching board info for {board_url}: {e}")
            return None
    
    def _extract_name_from_url(self, url):
        """Extract board name from URL as fallback"""
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-1].replace('-', ' ').title()
        return 'Unknown Board'
    
    def _extract_username_from_url(self, url):
        """Extract username from URL"""
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-2]
        return 'unknown'
    
    def normalize_url(self, url):
        """Normalize Pinterest URL to a standard format"""
        if not url.startswith('http'):
            url = 'https://' + url
        
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        # Ensure path ends with board format: /username/board/
        if not path.endswith('/'):
            path += '/'
        
        return f"https://{parsed.netloc}{path}"
    
    def get_user_info(self, username):
        """Get user profile information"""
        domains = ['www.pinterest.com', 'tr.pinterest.com', 'pinterest.com']
        
        for domain in domains:
            user_url = f"https://{domain}/{username}/"
            
            try:
                response = self.session.get(user_url, timeout=10)
                response.raise_for_status()
                
                # Extract display name
                display_name_match = re.search(r'"full_name":"([^"]+)"', response.text)
                display_name = display_name_match.group(1) if display_name_match else None
                
                # Fallback to username if display name is too short or missing
                if not display_name or len(display_name) < 2:
                    display_name = username
                
                # If we got a response, return basic info
                if response.status_code == 200:
                    return {
                        'username': username,
                        'display_name': display_name
                    }
            
            except Exception as e:
                print(f"Error fetching user info from {domain} for {username}: {e}")
                continue
        
        return None
