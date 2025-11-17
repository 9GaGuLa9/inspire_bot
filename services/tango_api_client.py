import requests
import uuid
import json
import base64
import re
from datetime import datetime
from typing import Tuple, Optional

class TangoAPIClient:
    def __init__(self, token_file="tango_token.json"):
        self.token_file = token_file
        self.device_id = None
        self.visitor_token = None
        self.token_expires = 0
        self._load_token()
    
    def _load_token(self):
        """Завантажує токен з файлу"""
        try:
            with open(self.token_file) as f:
                data = json.load(f)
                self.device_id = data.get("device_id")
                self.visitor_token = data.get("visitor_token")
                self.token_expires = data.get("expires", 0)
        except FileNotFoundError:
            pass
    
    def _save_token(self):
        """Зберігає токен у файл"""
        data = {
            "device_id": self.device_id,
            "visitor_token": self.visitor_token,
            "expires": self.token_expires,
            "expires_date": datetime.fromtimestamp(self.token_expires).isoformat()
        }
        with open(self.token_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _is_token_valid(self):
        """Перевіряє чи токен ще дійсний (з буфером 1 день)"""
        if not self.visitor_token:
            return False
        current_time = datetime.now().timestamp()
        return current_time < (self.token_expires - 86400)  # -1 день
    
    def _refresh_visitor_token(self):
        """Отримує новий visitor token"""
        # Генеруємо Device ID якщо немає
        if not self.device_id:
            self.device_id = str(uuid.uuid4()).replace("-", "")
        
        url = "https://gateway.tango.me/visitor-lobby/api/public/visitors/v1/check-in"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://tango.me",
            "Referer": "https://tango.me/",
            "Cookie": f"Tango-DeviceId={self.device_id}"
        }
        
        response = requests.post(
            url,
            headers=headers,
            params={"appId": "tango"},
            json={}
        )
        
        if response.status_code != 200:
            raise Exception(f"Не вдалося отримати токен: {response.status_code}")
        
        # Шукаємо Tango-VT в cookies
        for cookie in response.cookies:
            if cookie.name == "Tango-VT":
                self.visitor_token = cookie.value
                
                # Декодуємо JWT для отримання exp
                parts = self.visitor_token.split(".")
                if len(parts) >= 2:
                    payload_data = parts[1] + "=" * (4 - len(parts[1]) % 4)
                    payload = json.loads(base64.b64decode(payload_data))
                    self.token_expires = payload.get("exp", 0)
                
                self._save_token()
                exp_date = datetime.fromtimestamp(self.token_expires)
                print(f"✅ Токен оновлено. Дійсний до: {exp_date}")
                return
        
        raise Exception("Tango-VT не знайдено в відповіді")
    
    def _ensure_valid_token(self):
        """Перевіряє і оновлює токен якщо потрібно"""
        if not self._is_token_valid():
            print("🔄 Оновлення токену...")
            self._refresh_visitor_token()
    
    def _make_api_request(self, url: str, params: dict = None):
        """Виконує API запит з автоматичним оновленням токену"""
        self._ensure_valid_token()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://tango.me/",
            "Cookie": f"Tango-VT={self.visitor_token}"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code in [401, 403]:
            # Токен недійсний, примусово оновлюємо
            print("⚠️ Токен недійсний, примусове оновлення...")
            self._refresh_visitor_token()
            # Повторюємо запит з новим токеном
            headers["Cookie"] = f"Tango-VT={self.visitor_token}"
            response = requests.get(url, headers=headers, params=params)
        
        return response
    
    def convert_alias(self, alias: str) -> Optional[str]:
        """Конвертує alias в account ID"""
        url = "https://gateway.tango.me/visitors/profilealias/api/alias/convert"
        response = self._make_api_request(url, params={"alias": alias})
        
        if response.status_code == 200:
            return response.text.strip().strip('"')
        return None
    
    def get_profile(self, account_id: str) -> Optional[dict]:
        """Отримує інформацію про профіль користувача"""
        url = f"https://gateway.tango.me/proxycador/api/profiles/v2/single?id={account_id}&basicProfile=true&liveStats=true&followStats=true"

        response = self._make_api_request(url)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def extract_id_from_url(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Витягує ID або alias з URL Tango.me
        Повертає tuple: (id_or_alias, type) де type = 'id' або 'alias'
        """
        # Видаляємо пробіли та нормалізуємо URL
        url = url.strip()
        
        # Шаблони для різних типів URL
        patterns = [
            # https://tango.me/profile/123456789
            (r'tango\.me/profile/([a-zA-Z0-9_-]+)', 'id'),
            # https://tango.me/stream/123456789
            (r'tango\.me/stream/([a-zA-Z0-9_-]+)', 'stream'),
            # https://tango.me/username
            (r'tango\.me/([a-zA-Z0-9_-]+)$', 'alias'),
        ]
        
        for pattern, id_type in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), id_type
        
        return None
    
    def get_user_id_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Отримує user ID та ім'я з URL
        Повертає: (user_id, user_name)
        """
        extracted = self.extract_id_from_url(url)
        
        if not extracted:
            raise ValueError("Не вдалося розпізнати URL")
        
        identifier, id_type = extracted
        
        # Якщо це alias, спочатку конвертуємо в ID
        if id_type == 'alias':
            print(f"🔄 Конвертація alias '{identifier}' в ID...")
            account_id = self.convert_alias(identifier)
            if not account_id:
                raise Exception(f"Не вдалося конвертувати alias '{identifier}'")
        else:
            account_id = identifier
        
        # Отримуємо профіль
        print(f"📥 Завантаження профілю {account_id}...")
        profile = self.get_profile(account_id)
        
        if not profile:
            raise Exception(f"Не вдалося завантажити профіль {account_id}")
        
        # Витягуємо ім'я
        user_name = (
            profile.get("displayName")
            or profile.get("name")
            or profile.get("basicProfile", {}).get("firstName")
            or (profile.get("basicProfile", {}).get("aliases", [{}])[0].get("alias"))
            or "Unknown"
        )
        
        return account_id, user_name
    
    def __enter__(self):
        """Context manager enter"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass


# Тестування
if __name__ == "__main__":
    client = TangoAPIClient()
    
    # # Тестові URL
    # test_urls = [
    #     "https://tango.me/profile/zorich7",
    #     "https://tango.me/@zorich7",
    #     "https://tango.me/stream/123456789"
    # ]
    
    # for url in test_urls:
    #     print(f"\n{'='*60}")
    #     print(f"Тестування: {url}")
    #     print('='*60)
    #     try:
    #         user_id, user_name = client.get_user_id_from_url(url)
    #         print(f"✅ User ID: {user_id}")
    #         print(f"✅ User Name: {user_name}")
    #     except Exception as e:
    #         print(f"❌ Помилка: {e}")
