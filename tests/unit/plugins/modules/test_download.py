from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
from unittest.mock import patch, MagicMock
import pytest
from ansible_collections.cloudkrafter.nexus.plugins.modules.download import is_valid_version

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
    get_version_download_url
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

    # @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.requests')
    # @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.BeautifulSoup')
    # def test_get_version_download_url(self, mock_bs4, mock_requests):
    #     # Setup mock response
    #     mock_response = MagicMock()
    #     mock_response.text = self.mock_html
    #     mock_response.raise_for_status.return_value = None
    #     mock_requests.get.return_value = mock_response

    #     # Setup BeautifulSoup mock with find_all
    #     mock_soup = MagicMock()
    #     mock_bs4.return_value = mock_soup

    #     # Create mock links
    #     mock_link1 = MagicMock()
    #     mock_link1.get.return_value = 'https://download.sonatype.com/nexus/3/nexus-3.78.0-01-unix.tar.gz'
    #     mock_link2 = MagicMock()
    #     mock_link2.get.return_value = 'https://download.sonatype.com/nexus/3/nexus-3.77.0-01-unix.tar.gz'

    #     mock_soup.find_all.return_value = [mock_link1, mock_link2]

    #     result = get_version_download_url('3.78.0-01')
    #     assert result == 'https://download.sonatype.com/nexus/3/nexus-3.78.0-01-unix.tar.gz'

    # @patch('ansible.module_utils.basic.AnsibleModule')
    # @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.get_download_url')
    # @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.download_file')
    # def test_main_latest_success(self, mock_download_file, mock_get_url, mock_module):
    #     # Setup mocks
    #     mock_instance = setup_ansible_module_mock(mock_module, self.module_args)
    #     mock_get_url.return_value = 'https://example.com/nexus.tar.gz'
    #     mock_download_file.return_value = (True, "Success", "/tmp/nexus/nexus.tar.gz", 200)

    #     # Test main function
    #     main()  # Remove pytest.raises since we're not raising SystemExit anymore

    #     mock_instance.exit_json.assert_called_once_with(
    #         changed=True,
    #         download_url='https://example.com/nexus.tar.gz',
    #         msg="Success",
    #         destination="/tmp/nexus/nexus.tar.gz",
    #         status_code=200
    #     )

    # @patch('ansible.module_utils.basic.AnsibleModule')
    # def test_main_missing_version(self, mock_module):
    #     # Test when state is 'present' but version is missing
    #     self.module_args['state'] = 'present'
    #     mock_instance = setup_ansible_module_mock(mock_module, self.module_args)

    #     with pytest.raises(SystemExit):
    #         main()

    #     mock_instance.fail_json.assert_called_once_with(
    #         msg="When state is 'present', the 'version' parameter must be provided."
    #     )

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
