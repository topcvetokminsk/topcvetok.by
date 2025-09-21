import time
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from yandex_reviews_parser.parsers import Parser


class YandexParser:
    def __init__(self, company_id: int, domain_name: str = None, company_name : str = None):
        """
        @param id_yandex: ID Яндекс компании
        """
        if not domain_name or not company_name:
            raise ValueError("Параметры domain_name и company_name обязательны и не могут быть пустыми!")

        self.company_id = company_id
        self.domain_name = domain_name
        self.company_name = company_name

    def __open_page(self, chrome_version: int = None):
        """
        Внутренний метод для открытия страницы и инициализации парсера.
        @param chrome_version: Основная версия Chrome (например, 108).
                               Если None, uc.Chrome попытается определить автоматически.
        """
        url = f'https://{self.domain_name}/maps/org/{self.company_name}/{self.company_id}/reviews/'
        opts = uc.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-extensions')
        opts.add_argument('--disable-infobars')
        opts.add_argument('--window-size=1920,1080')
        opts.add_argument('--disable-notifications')
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-features=VizDisplayCompositor')
        opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')

        # Инициализация драйвера с учетом chrome_version
        if chrome_version:
            driver = uc.Chrome(options=opts, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=opts)

        driver.get(url)
        time.sleep(3)  # Даем время странице загрузиться
        wait = WebDriverWait(driver, 15)
        
        # Проверяем, не появилась ли капча
        try:
            # Ждем либо заголовок страницы, либо капчу
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'orgpage-header-view__header')]")),
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'captcha') or contains(text(), 'робат') or contains(text(), 'SmartCaptcha')]"))
            ))
            
            # Проверяем, есть ли капча
            captcha_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(text(), 'робат') or contains(text(), 'SmartCaptcha')]")
            if captcha_elements:
                print("Обнаружена капча на странице. Парсинг невозможен.")
                driver.quit()
                raise Exception("Обнаружена капча. Парсинг приостановлен.")
                
        except Exception as e:
            print(f"Ошибка при загрузке страницы: {e}")
            driver.quit()
            raise

        return Parser(driver)

    def parse(self, type_parse: str = 'default', chrome_version: int = None, callback=None) -> dict: # Добавляем chrome_version в parse
        """
        Функция получения данных.
        @param type_parse: Тип данных: 'default', 'company', 'reviews', 'reviews_incremental'.
        @param chrome_version: Основная версия Chrome (например, 108).
                               Если None, uc.Chrome попытается определить автоматически.
        @param callback: Функция callback для пошагового режима
        @return: Данные по запрошенному типу.
        """
        if type_parse not in {'default', 'company', 'reviews', 'reviews_incremental'}:
            print(f"Неизвестный тип парсинга: {type_parse}. Вернут пустой результат.")
            return {}

        parser = None

        try:
            parser = self.__open_page(chrome_version=chrome_version)

            if type_parse == 'default':
                return parser.parse_all_data()
            elif type_parse == 'company': # Используем elif для взаимоисключающих условий
                return parser.parse_company_info()
            elif type_parse == 'reviews': # Используем elif
                return parser.parse_reviews()
            elif type_parse == 'reviews_incremental': # Пошаговый режим
                return parser.parse_reviews_incremental(callback)

        except Exception as e:
            print(f"Error during parsing: {e}")

        finally:
            if parser and parser.driver:
                parser.driver.quit()

        return {}