#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2025, Brian Veltman <info@cloudkrafter.org>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
from unittest.mock import patch, MagicMock
import pytest
from ansible_collections.cloudkrafter.nexus.plugins.modules.download import (
    is_valid_version, get_latest_version, get_possible_package_names,
    validate_download_url, get_valid_download_urls
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

    @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.requests')
    def test_get_latest_version(self, mock_requests):
        """Test getting latest version from GitHub API"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "name": "release-3.78.0-01"
        }
        mock_requests.get.return_value = mock_response

        # Test successful case
        result = get_latest_version(validate_certs=True)
        assert result == '3.78.0-01'
        mock_requests.get.assert_called_once_with(
            "https://api.github.com/repos/sonatype/nexus-public/releases/latest",
            verify=True
        )

        # Reset mock for next test
        mock_requests.reset_mock()

        # Setup RequestException for error test
        mock_requests.exceptions = type('Exceptions', (), {
            'RequestException': Exception
        })
        mock_requests.get.side_effect = mock_requests.exceptions.RequestException("API Error")

        # Test API error
        with pytest.raises(Exception, match="Failed to fetch version from API"):
            get_latest_version(validate_certs=True)


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
def test_validate_download_url(mock_requests):
    """Test URL validation using HEAD requests"""
    # Setup mock responses
    mock_response_valid = MagicMock()
    mock_response_valid.ok = True
    mock_response_valid.status_code = 200

    mock_response_invalid = MagicMock()
    mock_response_invalid.ok = False
    mock_response_invalid.status_code = 404

    # Test valid URL
    mock_requests.head.return_value = mock_response_valid
    is_valid, status_code = validate_download_url("https://download.sonatype.com/nexus/3/test.tar.gz")
    assert is_valid is True
    assert status_code == 200

    # Test invalid URL
    mock_requests.head.return_value = mock_response_invalid
    is_valid, status_code = validate_download_url("https://download.sonatype.com/nexus/3/nonexistent.tar.gz")
    assert is_valid is False
    assert status_code == 404

    # Test connection error
    mock_requests.exceptions = MagicMock()
    mock_requests.exceptions.RequestException = Exception
    mock_requests.head.side_effect = mock_requests.exceptions.RequestException
    is_valid, status_code = validate_download_url("https://invalid.url")
    assert is_valid is False
    assert status_code is None


@patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.validate_download_url')
def test_get_valid_download_urls(mock_validate):
    """Test getting valid download URLs by checking headers"""
    # Setup mock responses for different URLs
    mock_validate.side_effect = [
        (True, 200),   # First URL is valid
        (False, 404),  # Second URL is invalid
        (True, 200),   # Third URL is valid
        (False, 404),  # Fourth URL is invalid
    ]

    # Test successful case
    base_url = "https://download.sonatype.com/nexus/3/"
    result = get_valid_download_urls('3.78.1-02', arch='aarch64', base_url=base_url)

    # Verify we got valid URLs
    assert len(result) == 2
    assert all(url.startswith(base_url) for url in result)
    assert all('3.78.1-02' in url for url in result)

    # Test invalid version
    mock_validate.reset_mock()
    with pytest.raises(ValueError, match="Invalid version format"):
        get_valid_download_urls('invalid')

    # Test when no valid URLs found
    mock_validate.reset_mock()
    mock_validate.side_effect = [(False, 404)] * 10  # All URLs return 404
    with pytest.raises(ValueError, match="No valid download URLs found"):
        get_valid_download_urls('3.78.1-02')


# @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.get_latest_version')
# @patch('ansible_collections.cloudkrafter.nexus.plugins.modules.download.get_valid_download_urls')
# def test_get_download_url(mock_get_valid_urls, mock_get_latest):
#     """Test URL selection based on state and version"""
#     base_url = 'https://download.sonatype.com/nexus/3/'
#     version = '3.78.0-01'

#     # Test latest version with single URL
#     mock_get_latest.return_value = version
#     mock_get_valid_urls.return_value = [f'{base_url}nexus-{version}-unix.tar.gz']

#     result = get_download_url(state='latest', validate_certs=True)
#     assert result == f'{base_url}nexus-{version}-unix.tar.gz'
#     mock_get_latest.assert_called_once_with(validate_certs=True)

#     # Reset mocks
#     mock_get_latest.reset_mock()
#     mock_get_valid_urls.reset_mock()

#     # Test present state with multiple URLs
#     urls = [
#         f'{base_url}nexus-unix-{version}.tar.gz',
#         f'{base_url}nexus-{version}-unix.tar.gz'
#     ]
#     mock_get_valid_urls.return_value = urls

#     with pytest.raises(ValueError, match="Multiple valid URLs found"):
#         get_download_url(state='present', version=version)

#     # Reset mocks
#     mock_get_valid_urls.reset_mock()

#     # Test invalid state
#     with pytest.raises(ValueError, match="Invalid state"):
#         get_download_url(state='invalid')

#     # Test missing version in present state
#     with pytest.raises(ValueError, match="Version must be provided"):
#         get_download_url(state='present')
