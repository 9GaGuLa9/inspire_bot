import sys
import os
import json
import datetime
import logging
from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from time import sleep
from configparser import ConfigParser
from typing import List, Dict, Any

class GifterSearcher:
    def __init__(self, config_path: str = "example.ini"):
        self.config_path = config_path
        self.driver = None
        self.duration = 0.5
        self.data = []
        self.current_time = datetime.datetime.now()
        self.setup_driver()
        
        # URL-и для різних категорій
        self.link_list = {
            "Popular": 'https://gateway.tango.me/proxycador/api/live/feeds/v1/byTags?tag=popular&pageCount=',
            "Nearby": 'https://gateway.tango.me/proxycador/api/live/feeds/v1/byTags?tag=nearby&pageCount=',
            "Following": 'https://gateway.tango.me/proxycador/api/live/feeds/v1/byTags?tag=following&pageCount=',
            "Recommended": 'https://gateway.tango.me/proxycador/api/live/feeds/v1/byTags?tag=hottest&pageCount='
        }
    
    def get_executable_path(self):
        """Отримання шляху до виконуваного файлу"""
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
        else:
            executable_path = os.path.abspath(__file__)
        return os.path.dirname(executable_path)
    
    def setup_driver(self):
        """Налаштування Chrome драйвера"""
        try:
            executable_path = self.get_executable_path()
            
            # Читання конфігурації
            initfile = os.path.join(executable_path, self.config_path)
            if not os.path.isfile(initfile):
                logging.error(f"Конфігураційний файл не знайдено: {initfile}")
                return False
            
            config = ConfigParser()
            config.read(initfile)
            
            # Перевірка необхідних секцій
            required_sections = ['chromedriver', 'delay', 'website']
            for section in required_sections:
                if not config.has_section(section):
                    logging.error(f"Відсутня секція: {section}")
                    return False
            
            driver_path = config.get('chromedriver', 'path')
            chrome_driver_path = os.path.join(executable_path, driver_path)
            self.duration = float(config.get("delay", "seconds"))
            
            # Налаштування Chrome опцій
            options = webdriver.ChromeOptions()
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
            options.add_argument('user-data-dir=C:\\Users\\Admin\\\\AppData\\Local\\Google\\Chrome\\User Data\\Default')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--ignore-certificate-errors')
            # options.add_argument('--headless')  # Безголовий режим для бота
            
            s = Service(chrome_driver_path)
            self.driver = webdriver.Chrome(service=s, options=options)
            return True
            
        except Exception as ex:
            logging.error(f"Помилка налаштування драйвера: {ex}")
            return False
    
    def search_gifters(self, gifter_ids: List[str], num_streamers: int = 50, categories: List[str] = None) -> Dict[str, Any]:
        """
        Пошук дарувальників у стрімах
        
        Args:
            gifter_ids: Список ID дарувальників для пошуку
            num_streamers: Кількість стрімерів для перевірки в кожній категорії
            categories: Список категорій для пошуку (за замовчуванням всі)
        
        Returns:
            Словник з результатами пошуку
        """
        if not self.driver:
            return {"error": "Драйвер не ініціалізовано"}
        
        if not gifter_ids:
            return {"error": "Список ID дарувальників порожній"}
        
        # Якщо категорії не вказані, використовуємо всі
        if categories is None:
            categories = list(self.link_list.keys())
        
        # Очищуємо дані перед початком пошуку
        self.data = []
        
        # Розрахунок кількості сторінок
        pages_count = num_streamers // 50 + (1 if num_streamers % 50 > 0 else 0)
        
        results = {
            "found_gifters": [],
            "total_found": 0,
            "searched_streamers": 0,
            "categories_searched": categories,
            "search_time": self.current_time.strftime("%d.%m.%Y_%H.%M"),
            "error": None
        }
        
        try:
            # Авторизація (перехід на головну сторінку)
            self.driver.get("https://tango.me/live/recommended")
            sleep(self.duration * 2)
            
            num_streamer = 1
            num_gifter = 1
            
            # Пошук по категоріях
            for category in categories:
                if category not in self.link_list:
                    continue
                
                print(f'Пошук у категорії "{category}"')
                link = self.link_list[category]
                
                # Пошук по сторінках
                for page in range(pages_count):
                    print(f"Сторінка: {page + 1}")
                    
                    # Перехід на API endpoint
                    api_url = link + str(page) + '&pageSize=50'
                    self.driver.get(api_url)
                    sleep(self.duration)
                    
                    page_source = self.driver.page_source
                    
                    try:
                        # Парсинг JSON відповіді
                        dataform = '{"stream":' + str(page_source).partition('"stream":')[2].partition(',"settings":')[0] + '}'
                        struct_streamer_id = json.loads(dataform)
                        
                        dataform_streamer = '{"stream":' + str(page_source).partition('"basicProfile":')[2].partition(',"liveStats":')[0] + '}'
                        struct_streamer_name = json.loads(dataform_streamer)
                        
                    except Exception as ex:
                        logging.error(f"Помилка парсингу JSON: {ex}")
                        continue
                    
                    # Отримання списків ID
                    stream_id_list = [stream_info['id'] for stream_info in struct_streamer_id['stream'].values()]
                    streamer_id_list = [stream_info['broadcasterId'] for stream_info in struct_streamer_id['stream'].values()]
                    
                    # Перевірка кожного стрім
                    for stream_id, streamer_id in zip(stream_id_list, streamer_id_list):
                        if num_streamer > num_streamers:
                            break
                        
                        if num_streamer % 25 == 0:
                            sleep(2)  # Пауза кожні 25 стрімерів
                        
                        print(f"Стрімер {num_streamer} з {num_streamers}: Знайдено {len(self.data)}")
                        
                        # Отримання списку дарувальників та глядачів стріму
                        gifters_url = f"https://gateway.tango.me/proxycador/api/public/v1/live/stream/social/v1/{stream_id}/topGifters?pageCount=0&pageSize=100&enableViewers=true"
                        self.driver.get(gifters_url)
                        sleep(self.duration)
                        
                        page_source = self.driver.page_source
                        
                        try:
                            # Очищення HTML та парсинг JSON
                            clean_data = str(page_source).replace('<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>', '').replace('</pre><div class="json-formatter-container"></div></body></html>', '').replace("\n'", "").replace("\n'", "")
                            struct = json.loads(clean_data)
                            
                        except Exception as ex:
                            logging.error(f"Помилка парсингу відповіді стріму: {ex}")
                            num_streamer += 1
                            continue
                        
                        # Отримання списків ID дарувальників та глядачів
                        try:
                            gifters_in_stream = [gifter["account"]["encryptedAccountId"] for gifter in struct.get("gifters", [])]
                        except Exception:
                            gifters_in_stream = []
                        
                        try:
                            viewers_in_stream = [viewer["account"]["encryptedAccountId"] for viewer in struct.get("viewers", [])]
                        except Exception:
                            viewers_in_stream = []
                        
                        # Перевірка наявності шуканих дарувальників
                        for search_id in gifter_ids:
                            if search_id in gifters_in_stream or search_id in viewers_in_stream:
                                # Визначаємо тип (дарувальник чи глядач)
                                user_type = "gifters" if search_id in gifters_in_stream else "viewers"
                                
                                # Знаходимо дані користувача
                                user_list = struct.get(user_type, [])
                                for user_item in user_list:
                                    if user_item['account']['encryptedAccountId'] == search_id:
                                        try:
                                            # Збір даних про знайденого дарувальника
                                            gifter_data = {
                                                "num": num_gifter,
                                                "ID стрімера": streamer_id,
                                                "ID дарувальника": user_item['account']['encryptedAccountId'],
                                                "Ім'я дарувальника": user_item['account'].get('firstName', '-'),
                                                "Кількість монет": user_item.get('creditsInStream', 'Глядач'),
                                                "Посилання дарувальника": f"https://tango.me/profile/{user_item['account']['encryptedAccountId']}",
                                                "Ім'я стрімера": struct_streamer_name['stream'][streamer_id].get('firstName', '-'),
                                                "Посилання на стрімера": f"https://tango.me/profile/{streamer_id}",
                                                "Посилання на стрім": f"https://tango.me/stream/{stream_id}",
                                                "VIP статус": user_item['account'].get('vipConfigId', '-'),
                                                "Гендер": user_item['account'].get('gender', '-'),
                                                "Підписка на стрімера": user_item.get('isSubscriber', '-'),
                                                "Фан рівень": user_item.get('subscriptionLevel', '-'),
                                                "Інкогніто": user_item.get('incognito', '-'),
                                                "Тип": user_type,
                                                "Категорія": category
                                            }
                                            
                                            self.data.append(gifter_data)
                                            num_gifter += 1
                                            
                                            print(f"Знайдено: {gifter_data['Ім`я дарувальника']} -> {gifter_data['Ім`я стрімера']}")
                                            
                                        except Exception as ex:
                                            logging.error(f"Помилка збору даних: {ex}")
                                            continue
                        
                        num_streamer += 1
                        results["searched_streamers"] = num_streamer - 1
                
                # Скидаємо лічильник стрімерів для наступної категорії
                num_streamer = 1
            
            # Підготовка результатів
            results["found_gifters"] = self.data
            results["total_found"] = len(self.data)
            
            return results
            
        except Exception as ex:
            logging.error(f"Помилка пошуку: {ex}")
            results["error"] = str(ex)
            return results
    
    def save_results(self, results: Dict[str, Any], save_path: str = None) -> str:
        """Збереження результатів пошуку в JSON файл"""
        try:
            if save_path is None:
                executable_path = self.get_executable_path()
                save_path = os.path.join(executable_path, f'search_results_{self.current_time.strftime("%d.%m.%Y_%H.%M")}.json')
            
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(results, file, indent=4, ensure_ascii=False)
            
            return save_path
            
        except Exception as ex:
            logging.error(f"Помилка збереження: {ex}")
            return None
    
    def close(self):
        """Закриття браузера"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()