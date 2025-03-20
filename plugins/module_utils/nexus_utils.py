REQUESTS_IMP_ERR = None

try:
    import requests
except ImportError as e:
    REQUESTS_IMP_ERR = str(e)
    requests = None


__all__ = [
    'requests'
]

