import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ssl
from src.utils.LogManager import get_logger

logger = get_logger()

class TlsV1HttpAdapter(HTTPAdapter):
    """
    A custom HTTP adapter that forces TLSv1.2 and uses a more compatible cipher suite.
    This helps to connect to servers with specific SSL/TLS requirements.
    """
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # Create a custom SSL context
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Set the minimum TLS version to 1.2, which is widely supported
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Use a more forgiving cipher list to improve compatibility.
        # This list is a common recommendation to mimic browser-like behavior.
        ciphers = (
            "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:"
            "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"
            "DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"
        )
        context.set_ciphers(ciphers)
        
        # Pass the custom context to the pool manager
        pool_kwargs['ssl_context'] = context
        super().init_poolmanager(connections, maxsize, block, **pool_kwargs)


_session = None

def get_session():
    """
    Returns a pre-configured, singleton requests.Session object.

    The session is configured with:
    1. A retry mechanism for transient network errors.
    2. A custom TLS adapter to improve compatibility with picky servers.
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

        # Create the custom adapter
        adapter = TlsV1HttpAdapter(max_retries=retries)

        # Mount the adapter to handle all HTTPS requests
        _session.mount("https://", adapter)
        
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
    Unified HTTP content fetching interface using a two-stage approach.

    This is the recommended method for all HTTP GET requests in the project.
    It provides:
    1. A primary attempt using a custom session with a secure TLSv1.2+ adapter.
    2. A fallback to a standard, unverified request if the primary attempt fails
       due to an SSL error, which avoids adapter/context conflicts.

    Args:
        url (str): The URL to fetch.
        timeout (int): Request timeout in seconds.

    Returns:
        str: The response content as text.

    Raises:
        Exception: If all connection attempts fail.
    """
    # --- Attempt 1: Use the custom, secure session ---
    try:
        session = get_session()
        logger.info(f"Fetching {url} with custom TLS adapter and SSL verification")
        response = session.get(url, timeout=timeout, verify=True)
        response.raise_for_status()
        logger.info(f"Successfully fetched {url}")
        return response.text
    except requests.exceptions.SSLError as e:
        logger.warning(f"SSL verification failed for {url} with custom adapter: {e}")
        logger.warning("Retrying with a standard library call WITHOUT SSL verification (insecure)...")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url} on initial attempt: {e}")
        raise Exception(f"Failed to fetch {url} using all available methods") from e

    # --- Attempt 2: Fallback using a standard requests call with verify=False ---
    try:
        # Suppress the warning about unverified HTTPS requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Use a completely standard requests call to avoid any ssl.Context conflicts
        response = requests.get(
            url,
            timeout=timeout,
            verify=False,
            headers={'User-Agent': get_session().headers['User-Agent']} # Re-use the user agent
        )
        response.raise_for_status()

        logger.warning(f"Successfully fetched {url} without SSL verification")
        # Re-enable warnings after our call
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"All methods failed for {url}: {e}")
        raise Exception(f"Failed to fetch {url} using all available methods") from e
