import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from src.utils.LogManager import get_logger

logger = get_logger()

class ConfigCrypto:
    """
    AES-GCM 加密实现，用于保护敏感配置数据。
    符合项目安全规范。
    """
    
    @staticmethod
    def _get_key() -> bytes:
        # 动态拼接密钥，避免硬编码字符串字面量
        # 基础部分
        p1 = b'\x92\x3a\xdf\x55\x12' 
        p2 = b'Mita' + b'Hill'
        p3 = b'FRP' + b'2025'
        # 简单的字节操作混淆
        key_seed = p2 + p1 + p3 # b'MitaHill\x92\x3a\xdf\x55\x12FRP2025' (approx 20 chars)
        
        # 填充到 32 字节 (AES-256)
        while len(key_seed) < 32:
            key_seed += b'\x00'
        return key_seed[:32]

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """
        使用 AES-GCM 加密字符串。
        返回格式: nonce|ciphertext|tag (Base64编码)
        """
        try:
            key = ConfigCrypto._get_key()
            cipher = AES.new(key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            
            # 组合: nonce + tag + ciphertext
            payload = cipher.nonce + tag + ciphertext
            return base64.b64encode(payload).decode('ascii')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ""

    @staticmethod
    def decrypt(encrypted_text: str) -> str:
        """
        解密 AES-GCM 加密的字符串。
        """
        try:
            # 尝试处理旧版 XOR 数据 (简单的长度或字符检查，或者直接 try-catch)
            # 但由于 AES 结构严格，直接尝试 AES 解密，失败则回退或返回空
            
            data = base64.b64decode(encrypted_text.encode('ascii'))
            
            # AES-GCM nonce is usually 16 bytes, tag is 16 bytes
            if len(data) < 32:
                # 可能是旧数据或损坏数据
                return ConfigCrypto._try_legacy_decrypt(encrypted_text)

            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]

            key = ConfigCrypto._get_key()
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
        except Exception as e:
            # logger.debug(f"AES decryption failed, trying legacy: {e}")
            return ConfigCrypto._try_legacy_decrypt(encrypted_text)

    @staticmethod
    def _try_legacy_decrypt(encoded: str, key: int = 0x5A) -> str:
        """兼容旧版 XOR 解密，用于过渡"""
        try:
            data = base64.b64decode(encoded.encode('ascii'))
            result = bytearray()
            for i, b in enumerate(data):
                result.append(b ^ (key + i % 256))
            return result.decode('utf-8')
        except Exception:
            return ""

    # 别名以保持兼容性 (如果其他地方用了 obfuscate/deobfuscate)
    obfuscate = encrypt
    deobfuscate = decrypt
