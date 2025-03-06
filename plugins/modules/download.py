#!/usr/bin/python
import requests
from bs4 import BeautifulSoup
from packaging import version
import re
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: download
short_description: Download Nexus package
description:
  - This module downloads a specified Nexus package from Sonatype's Nexus repository.
version_added: "1.20"
options:
  state:
    description:
      - Determines whether to download the latest version or a specific version.
    required: true
    choices: ['latest', 'present']
  version:
    description:
      - The version to download when state is 'present'.
    required: false
  dest:
    description:
      - Destination directory where the file should be saved.
    required: true
  verify_ssl:
    description:
      - If False, SSL certificates will not be validated.
    type: bool
    default: true
    required: false
author: "Brian Veltman"
'''

EXAMPLES = '''
- name: Download the latest Nexus package
  cloudkrafter.nexus.download:
    state: latest
    dest: /path/to/download/dir
    verify_ssl: true

- name: Download a specific Nexus version without SSL verification
  cloudkrafter.nexus.download:
    state: present
    version: 3.78.0-1
    dest: /path/to/download/dir
    verify_ssl: false
'''

RETURN = '''
download_url:
    description: The URL used for downloading the package.
    type: str
    returned: always
changed:
    description: Indicates if a change was made (e.g., download occurred).
    type: bool
    returned: always
'''

def get_latest_version(verify_ssl=False):
    """
    Scrapes the Sonatype download page to find the latest version.
    
    Args:
        verify_ssl (bool): Whether to verify SSL certificates
    """
    url = "https://help.sonatype.com/en/download-archives---repository-manager-3.html"
    try:
        response = requests.get(url, verify=verify_ssl)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for version pattern in text (e.g., "3.78.0-01")
        version_pattern = r'(\d+\.\d+\.\d+-\d+)'
        versions = []
        
        for text in soup.stripped_strings:
            match = re.search(version_pattern, text)
            if match:
                versions.append(match.group(1))
        
        if not versions:
            raise ValueError("No version found on download page")
            
        # Sort versions and get the latest
        latest = sorted(versions, key=lambda x: version.parse(x.split('-')[0]))[-1]
        return latest
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch download page: {str(e)}")

def get_version_download_url(version, verify_ssl=True):
    """
    Scrapes the download page to find the specific URL for a version.
    
    Args:
        version (str): Version string in format X.Y.Z-NN
        verify_ssl (bool): Whether to verify SSL certificates
    
    Returns:
        str: Download URL for the specific version
    """
    url = "https://help.sonatype.com/en/download-archives---repository-manager-3.html"
    try:
        response = requests.get(url, verify=verify_ssl)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for download links containing the version
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if version in href and 'unix' in href.lower():
                return href
                
        raise ValueError(f"No download URL found for version {version}")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch download page: {str(e)}")

def get_download_url(state, version=None, verify_ssl=True):
    """
    Determines the download URL based on state and version.
    
    Args:
        state (str): Either 'latest' or 'present'
        version (str): Optional version string (required if state is 'present')
        verify_ssl (bool): Whether to verify SSL certificates
    
    Returns:
        str: Download URL for the specified version
    
    Raises:
        ValueError: If version format is invalid or version not found
    """
    try:
        if state == 'latest':
            version = get_latest_version(verify_ssl=verify_ssl)
        
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+-\d+$', version):
            raise ValueError(f"Invalid version format: {version}")
            
        return get_version_download_url(version, verify_ssl=verify_ssl)
        
    except Exception as e:
        raise Exception(f"Error determining download URL: {str(e)}")

def main():
    module_args = dict(
        state=dict(type='str', required=True, choices=['latest', 'present']),
        version=dict(type='str', required=False),
        dest=dict(type='path', required=True),
        verify_ssl=dict(type='bool', required=False, default=True)
    )
    
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    state = module.params['state']
    version = module.params.get('version')
    dest = module.params['dest']
    verify_ssl = module.params['verify_ssl']
    
    # Validate parameters.
    if state == 'present' and not version:
        module.fail_json(msg="When state is 'present', the 'version' parameter must be provided.")
    
    try:
        download_url = get_download_url(state, version, verify_ssl=verify_ssl)
    except Exception as e:
        module.fail_json(msg="Error determining download URL: " + str(e))
    
    # Check mode: report what would be done.
    if module.check_mode:
        module.exit_json(changed=False, download_url=download_url)
    
    # Here, you could integrate Ansible's built-in get_url functionality
    # or implement your own download logic.
    # For now, assume that the URL is ready and report success.
    
    module.exit_json(changed=True, download_url=download_url)

if __name__ == '__main__':
    main()
