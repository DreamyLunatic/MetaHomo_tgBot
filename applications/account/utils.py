# utils/telegram_auth.py

import hashlib
import hmac
import time

def verify_telegram_auth(data: dict, bot_token: str, max_age=86400):
    check_hash = data.pop('hash')
    auth_date = int(data.get('auth_date', 0))
    
    # Проверка срока действия (1 день по умолчанию)
    if time.time() - auth_date > max_age:
        return False

    sorted_data = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, sorted_data.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(calculated_hash, check_hash)
