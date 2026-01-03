"""
AnhMin Audio - Update Checker
Check for new versions from GitHub Releases
"""

import requests
from typing import Optional, Dict
from packaging import version


class UpdateChecker:
    """Check for updates from GitHub releases."""

    def __init__(self, repo_owner: str, repo_name: str, current_version: str):
        """
        Initialize update checker.

        Args:
            repo_owner: GitHub username
            repo_name: Repository name
            current_version: Current app version (e.g., "1.0.0")
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version.lstrip('v')  # Remove 'v' prefix if exists
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def check_for_updates(self) -> Optional[Dict]:
        """
        Check if a new version is available.

        Returns:
            Dict with update info if available, None otherwise.
            Format: {
                'version': '1.0.1',
                'download_url': 'https://...',
                'changelog': 'Release notes...',
                'size': 1024000  # bytes
            }
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()

            # Parse version
            latest_version = release_data['tag_name'].lstrip('v')

            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                # Find download link from assets
                download_url = None
                file_size = 0
                file_name = None

                # First try to find download_link.txt (for large files on Google Drive/OneDrive)
                for asset in release_data.get('assets', []):
                    if asset['name'] == 'download_link.txt':
                        # Download the .txt file to read the actual download URL
                        try:
                            txt_response = requests.get(asset['browser_download_url'], timeout=10)
                            txt_response.raise_for_status()
                            download_url = txt_response.text.strip()
                            # File size unknown for external links
                            file_size = 0
                            file_name = f"AnhMinAudio-v{latest_version}.zip"
                        except:
                            pass
                        break

                # If no download_link.txt, try to find .zip file directly
                if not download_url:
                    for asset in release_data.get('assets', []):
                        if asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            file_size = asset['size']
                            file_name = asset['name']
                            break

                # Fallback to .exe if no .zip found
                if not download_url:
                    for asset in release_data.get('assets', []):
                        if asset['name'].endswith('.exe'):
                            download_url = asset['browser_download_url']
                            file_size = asset['size']
                            file_name = asset['name']
                            break

                if not download_url:
                    return None

                return {
                    'version': latest_version,
                    'download_url': download_url,
                    'file_name': file_name,
                    'changelog': release_data.get('body', 'Không có thông tin chi tiết.'),
                    'size': file_size,
                    'published_at': release_data.get('published_at', '')
                }

            return None

        except requests.RequestException as e:
            print(f"Error checking for updates: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
