import base64

class ConfigCrypto:
    """简单的配置混淆加密，防止明文泄露token"""
    @staticmethod
    def obfuscate(text: str, key: int = 0x5A) -> str:
        result = bytearray()
        for i, c in enumerate(text.encode('utf-8')):
            result.append(c ^ (key + i % 256))
        return base64.b64encode(result).decode('ascii')
    
    @staticmethod
    def deobfuscate(encoded: str, key: int = 0x5A) -> str:
        data = base64.b64decode(encoded.encode('ascii'))
        result = bytearray()
        for i, b in enumerate(data):
            result.append(b ^ (key + i % 256))
        return result.decode('utf-8')
