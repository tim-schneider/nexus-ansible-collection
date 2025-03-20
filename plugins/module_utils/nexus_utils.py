REQUESTS_IMP_ERR = None
URLLIB3_IMP_ERR = None

try:
    import requests
except ImportError as e:
    REQUESTS_IMP_ERR = str(e)
    requests = None

try:
    import urllib3
except ImportError:
    urllib3 = None


__all__ = [
    'requests',
    'urllib3'
]

