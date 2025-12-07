import subprocess
import ssl
import urllib.request
import urllib.error
from src.utils.LogManager import get_logger

logger = get_logger()

def fetch_url_content(url, timeout=10):
    """
    Fetches content from a URL using multiple methods to ensure compatibility.
    First tries Python's urllib with proper SSL configuration,
    then falls back to PowerShell if needed.
    """
    # Create request with browser-like headers (used in multiple methods)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    # Method 1: Try with urllib and custom SSL context
    try:
        # Create a custom SSL context with TLS 1.2+ support
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Try to fetch with the custom context
        with urllib.request.urlopen(req, context=context, timeout=timeout) as response:
            content = response.read()
            # Decode the content
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            return content

    except (urllib.error.URLError, ssl.SSLError) as e:
        logger.warning(f"urllib failed for {url}: {e}, trying PowerShell method...")

        # Method 2: Fall back to PowerShell method
        try:
            return fetch_url_content_powershell(url, timeout)
        except Exception as ps_error:
            logger.error(f"PowerShell method also failed: {ps_error}")

            # Method 3: Try urllib without SSL verification (less secure, last resort)
            try:
                logger.warning("Attempting connection without SSL verification (insecure)...")
                insecure_context = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=insecure_context, timeout=timeout) as response:
                    content = response.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    logger.warning("Successfully fetched content without SSL verification")
                    return content
            except Exception as final_error:
                logger.error(f"All methods failed for {url}: {final_error}")
                raise Exception(f"Failed to fetch {url} using all available methods") from final_error

    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise

def fetch_url_content_powershell(url, timeout=10):
    """
    Fetches content from a URL by shelling out to PowerShell's WebClient.
    This is a last-resort workaround for servers with broken SSL/TLS implementations
    that are incompatible with Python's networking stack.
    """
    try:
        # This command tells PowerShell to use TLS 1.2, then downloads the string.
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            f"[System.Net.ServicePointManager]::SecurityProtocol = 'Tls12'; (New-Object System.Net.WebClient).DownloadString('{url}')"
        ]

        # Execute the command, hiding the window.
        # Don't specify encoding - let subprocess auto-detect system encoding (GBK/CP936 on Chinese Windows)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        return result.stdout

    except subprocess.CalledProcessError as e:
        raise Exception(f"PowerShell download failed with exit code {e.returncode}: {e.stderr}") from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred while running PowerShell downloader: {e}") from e
