from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
from unittest.mock import patch, MagicMock
import pytest
from ansible_collections.cloudkrafter.nexus.plugins.modules.download import (
    is_valid_version, get_latest_version, get_version_download_url, get_possible_package_names, scrape_download_page
)

@pytest.mark.parametrize('version,expected', [
    ('3.78.0-01', True),
    ('3.78.1-02', True),
    ('3.0.0-01', True),
    ('3.78.0', False),
    ('3.78-01', False),
    ('3.78.0.1-01', False),
    ('3.78.0-1', True),
    ('invalid', False),
    ('', False),
    (None, False),
])
def test_is_valid_version(version, expected):
    """Test version string validation"""
    result = is_valid_version(version)
    assert result == expected


# Mock the requests, bs4, and packaging imports before importing the module
sys.modules['requests'] = MagicMock()
bs4_mock = MagicMock()
BeautifulSoup = bs4_mock.BeautifulSoup
sys.modules['bs4'] = bs4_mock
sys.modules['packaging'] = MagicMock()
sys.modules['packaging.version'] = MagicMock()
sys.modules['urllib3'] = MagicMock()


# Update the packaging version mock to handle version comparisons
version_mock = MagicMock()


class MockVersion:
    def __init__(self, version_str):
        self.version_str = version_str

    def __lt__(self, other):
        return self.version_str < other.version_str

    def __gt__(self, other):
        return self.version_str > other.version_str


def mock_parse(version_str):
    return MockVersion(version_str)


version_mock.parse = mock_parse
sys.modules['packaging.version'] = version_mock

# Now import the module under test
from ansible_collections.cloudkrafter.nexus.plugins.modules.download import (
    get_latest_version,
    get_version_download_url,
    get_possible_package_names
)


def setup_ansible_module_mock(mock_module, params=None):
    """Helper to setup common AnsibleModule mock attributes"""
    mock_instance = MagicMock()
    mock_module.return_value = mock_instance
    mock_instance.params = params or {}
    mock_instance.check_mode = False

    # Don't set side effects that raise SystemExit
    mock_instance.exit_json = MagicMock()
    mock_instance.fail_json = MagicMock()

    return mock_instance


@patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.HAS_DEPS', True)
class TestNexusDownloadModule:
    def setup_method(self):
        self.module_args = {
            'state': 'latest',
            'dest': '/tmp/nexus',
            'validate_certs': True,
            'version': None,
            'arch': None
        }

        self.mock_html = '''
        <html><body>
            <div>
                <p>Release Notes for 3.78.0-01</p>
                <p>Release Notes for 3.77.0-01</p>
                <a href="https://download.sonatype.com/nexus/3/nexus-3.78.0-01-unix.tar.gz">nexus-3.78.0-01-unix.tar.gz</a>
                <a href="https://download.sonatype.com/nexus/3/nexus-3.77.0-01-unix.tar.gz">nexus-3.77.0-01-unix.tar.gz</a>
            </div>
        </body></html>
        '''

    @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.requests')
    @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.BeautifulSoup')
    @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.version')
    def test_get_latest_version(self, mock_version, mock_bs4, mock_requests):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = self.mock_html
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        # Setup BeautifulSoup mock
        mock_soup = MagicMock()
        mock_bs4.return_value = mock_soup
        mock_soup.stripped_strings = [
            'Release Notes for 3.78.0-01',
            'Release Notes for 3.77.0-01'
        ]

        # Setup version parsing mock
        mock_version.parse = mock_parse

        result = get_latest_version(validate_certs=True)
        assert result == '3.78.0-01'
        mock_requests.get.assert_called_once_with(
            "https://help.sonatype.com/en/download-archives---repository-manager-3.html",
            verify=True
    )


    # @patch('ansible.module_utils.basic.AnsibleModule')
    # @patch('sys.stdin')
    # def test_check_mode(self, mock_stdin, mock_module):
    #     mock_stdin.buffer.read.return_value = b'{}'
    #     mock_instance = setup_ansible_module_mock(mock_module, self.module_args)
    #     mock_instance.check_mode = True

    #     with patch('os.path.exists', return_value=False):
    #         with patch.dict('sys.modules', {'requests': MagicMock(), 'bs4': MagicMock()}):
    #             with patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.get_download_url') as mock_get_url:
    #                 mock_get_url.return_value = 'https://example.com/nexus.tar.gz'
    #                 with pytest.raises(SystemExit):
    #                     main()

    #     mock_instance.exit_json.assert_called_once()
    #     args = mock_instance.exit_json.call_args[1]
    #     assert args['changed'] is True
    #     assert 'download_url' in args


@pytest.mark.parametrize('version,arch,java_version,expected', [
    (
        '3.78.0-01',
        None,
        None,
        [
            'nexus-3.78.0-01-unix.tar.gz',
            'nexus-unix-3.78.0-01.tar.gz'
        ]
    ),
    (
        '3.78.0-01',
        'aarch64',
        None,
        [
            'nexus-unix-aarch64-3.78.0-01.tar.gz',
            'nexus-aarch64-unix-3.78.0-01.tar.gz',
            'nexus-3.78.0-01-unix.tar.gz',
            'nexus-unix-3.78.0-01.tar.gz'
        ]
    ),
    (
        '3.78.0-01',
        None,
        'java11',
        [
            'nexus-unix-3.78.0-01-java11.tar.gz',
            'nexus-3.78.0-01-unix-java11.tar.gz',
            'nexus-3.78.0-01-unix.tar.gz',
            'nexus-unix-3.78.0-01.tar.gz'
        ]
    ),
    (
        '3.78.0-01',
        'aarch64',
        'java11',
        [
            'nexus-unix-aarch64-3.78.0-01.tar.gz',
            'nexus-aarch64-unix-3.78.0-01.tar.gz',
            'nexus-unix-3.78.0-01-java11.tar.gz',
            'nexus-3.78.0-01-unix-java11.tar.gz',
            'nexus-3.78.0-01-unix.tar.gz',
            'nexus-unix-3.78.0-01.tar.gz'
        ]
    ),
])
def test_get_possible_package_names(version, arch, java_version, expected):
    """Test generation of possible package names"""
    result = get_possible_package_names(version, arch, java_version)
    assert result == expected


@patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.requests')
@patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.BeautifulSoup')
def test_scrape_download_page(mock_bs4, mock_requests):
    """Test scraping of download page"""
    # Setup mock response for successful case
    mock_response = MagicMock()
    mock_response.text = '<html><body>Test content</body></html>'
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Setup BeautifulSoup mock
    mock_soup = MagicMock()
    mock_bs4.return_value = mock_soup

    # Test successful scraping
    url = "https://test.com"
    result = scrape_download_page(url, validate_certs=True)
    
    assert result == mock_soup
    mock_requests.get.assert_called_once_with(url, verify=True)
    mock_bs4.assert_called_once_with(mock_response.text, 'html.parser')

    # Test request failure
    mock_requests.get.reset_mock()
    mock_requests.exceptions = MagicMock()
    mock_requests.exceptions.RequestException = Exception
    mock_requests.get.side_effect = mock_requests.exceptions.RequestException("Connection error")
    
    with pytest.raises(Exception) as exc_info:
        scrape_download_page(url, validate_certs=False)
    
    assert "Failed to fetch download page" in str(exc_info.value)
    mock_requests.get.assert_called_once_with(url, verify=False)
