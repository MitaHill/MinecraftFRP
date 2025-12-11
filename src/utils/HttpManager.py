import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ssl
from src.utils.LogManager import get_logger

logger = get_logger()

_session = None

def get_session():
    """
    Returns a pre-configured, singleton requests.Session object.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        
        # Configure retry mechanism
        retries = Retry(
            total=3,  # Total number of retries
            backoff_factor=0.5,  # Delay between retries = {0.5, 1, 2} seconds
            status_forcelist=[500, 502, 503, 504],  # Retry on these server errors
            allowed_methods=frozenset(['HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        )

        # Mount standard adapter with retry logic
        adapter = HTTPAdapter(max_retries=retries)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
        
        # Set a default timeout for all requests
        _session.timeout = 15  # seconds
        
        # Set a browser-like User-Agent
        _session.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

    return _session


def fetch_url_content(url, timeout=10):
    """
    Unified HTTP content fetching interface.
    """
    try:
        session = get_session()
        # logger.info(f"Fetching {url}") # Reduce noise
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        # Return empty string on failure, let caller handle it
        return "" 

