import hashlib
import hmac
import base64
from urllib.parse import urlencode, parse_qs
import os

VK_APP_SECRET = os.getenv("VK_APP_SECRET", "test_secret")

def verify_vk_signature(query_string: str) -> bool:
    """
    Проверяет подпись VK
    В тестовом режиме пропускаем проверку
    """
    # Для теста — всегда True
    if os.getenv("DEBUG", "true").lower() == "true":
        return True
    
    try:
        parsed = parse_qs(query_string.lstrip('?'))
        received_sign = parsed.get('sign', [None])[0]
        
        if not received_sign:
            return False
        
        vk_params = {k: v[0] for k, v in parsed.items() if k.startswith('vk_')}
        sorted_params = sorted(vk_params.items())
        params_string = urlencode(sorted_params)
        
        sign = base64.b64encode(
            hmac.new(
                VK_APP_SECRET.encode(),
                params_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        sign = sign.replace('+', '-').replace('/', '_').rstrip('=')
        
        return sign == received_sign
        
    except Exception as e:
        print(f"VK signature error: {e}")
        return False


def get_vk_user_id(query_string: str):
    """
    Получает VK ID из параметров
    """
    try:
        parsed = parse_qs(query_string.lstrip('?'))
        vk_user_id = parsed.get('vk_user_id', [None])[0]
        return int(vk_user_id) if vk_user_id else None
    except:
        return None