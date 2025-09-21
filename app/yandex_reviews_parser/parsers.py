import time
from dataclasses import asdict

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

from yandex_reviews_parser.helpers import ParserHelper
from yandex_reviews_parser.storage import Info, Review


class Parser:
    def __init__(self, driver):
        self.driver = driver

    def __scroll_to_bottom(self) -> None:
        """
        Скроллим список до последнего отзыва
        :return: None
        """
        wait = WebDriverWait(self.driver, 10)
        last_count = 0
        
        while True:
            # Получаем текущее количество отзывов
            try:
                elements = wait.until(EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "business-reviews-card-view__review")
                ))
                current_count = len(elements)
                
                if current_count == last_count:
                    # Если количество не изменилось, значит мы доскроллили до конца
                    break
                    
                last_count = current_count
                
                # Скроллим к последнему элементу
                if elements:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});",
                        elements[-1]
                    )
                    
                # Ждем загрузки новых элементов
                time.sleep(2)
                
                # Проверяем, что страница загрузилась
                try:
                    wait.until(EC.presence_of_element_located(
                        (By.CLASS_NAME, "business-reviews-card-view__review")
                    ))
                except TimeoutException:
                    break
                    
            except (StaleElementReferenceException, TimeoutException):
                break

    def __get_data_item(self, elem):
        """
        Спарсить данные по отзыву
        :param elem: Отзыв из списка
        :return: Словарь
        {
            name: str
            icon_href: Union[str, None]
            date: float
            text: str
            stars: float
        }
        """
        try:
            # Безопасное получение имени
            try:
                name = elem.find_element(By.XPATH, ".//span[@itemprop='name']").text
            except (NoSuchElementException, StaleElementReferenceException):
                name = None

            # Безопасное получение иконки
            try:
                icon_elem = elem.find_element(By.XPATH, ".//div[@class='user-icon-view__icon']")
                icon_href = icon_elem.get_attribute('style')
                if icon_href and '"' in icon_href:
                    icon_href = icon_href.split('"')[1]
                else:
                    icon_href = None
            except (NoSuchElementException, StaleElementReferenceException):
                icon_href = None

            # Безопасное получение даты
            try:
                date = elem.find_element(By.XPATH, ".//meta[@itemprop='datePublished']").get_attribute('content')
            except (NoSuchElementException, StaleElementReferenceException):
                date = None

            # Безопасное получение текста отзыва
            try:
                body_text_container = elem.find_element(By.CSS_SELECTOR, ".business-review-view__body")
                try:
                    expand_button = body_text_container.find_element(By.CSS_SELECTOR,
                                                                     ".business-review-view__expand[role='button']")
                    if expand_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", expand_button)
                        time.sleep(0.7)
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

                text_elem = elem.find_element(By.XPATH, ".//div[@class='spoiler-view__text']/span[@class=' spoiler-view__text-container']")
                text = text_elem.text
            except (NoSuchElementException, StaleElementReferenceException):
                text = None
                
            # Безопасное получение звезд
            try:
                stars_elements = elem.find_elements(By.XPATH, ".//div[@class='business-rating-badge-view__stars _spacing_normal']/span")
                stars = ParserHelper.get_count_star(stars_elements)
            except (NoSuchElementException, StaleElementReferenceException):
                stars = 0

            # Безопасное получение ответа
            try:
                answer_elem = elem.find_element(By.CLASS_NAME, "business-review-view__comment-expand")
                if answer_elem and answer_elem.is_displayed():
                    self.driver.execute_script("arguments[0].click()", answer_elem)
                    time.sleep(0.5)
                    answer = elem.find_element(By.CLASS_NAME, "business-review-comment-content__bubble").text
                else:
                    answer = None
            except (NoSuchElementException, StaleElementReferenceException):
                answer = None
                
        except StaleElementReferenceException:
            # Если элемент стал устаревшим, возвращаем пустые данные
            return {
                'name': None,
                'icon_href': None,
                'date': 0,
                'text': None,
                'stars': 0,
                'answer': None
            }
            
        item = Review(
            name=name,
            icon_href=icon_href,
            date=ParserHelper.form_date(date),
            text=text,
            stars=stars,
            answer=answer
        )
        return asdict(item)

    def __get_data_campaign(self) -> dict:
        """
        Получаем данные по компании.
        :return: Словарь данных
        {
            name: str
            rating: float
            count_rating: int
            stars: float
        }
        """
        try:
            xpath_name = ".//h1[@class='orgpage-header-view__header']"
            name = self.driver.find_element(By.XPATH, xpath_name).text
        except NoSuchElementException:
            name = None
        try:
            xpath_rating_block = ".//div[@class='business-summary-rating-badge-view__rating-and-stars']"
            rating_block = self.driver.find_element(By.XPATH, xpath_rating_block)
            xpath_rating = ".//div[@class='business-summary-rating-badge-view__rating']/span[contains(@class, 'business-summary-rating-badge-view__rating-text')]"
            rating = rating_block.find_elements(By.XPATH, xpath_rating)
            rating = ParserHelper.format_rating(rating)
            xpath_count_rating = ".//div[@class='business-summary-rating-badge-view__rating-count']/span[@class='business-rating-amount-view _summary']"
            count_rating_list = rating_block.find_element(By.XPATH, xpath_count_rating).text
            count_rating = ParserHelper.list_to_num(count_rating_list)
            xpath_stars = ".//div[@class='business-rating-badge-view__stars _spacing_normal']/span"
            stars = ParserHelper.get_count_star(rating_block.find_elements(By.XPATH, xpath_stars))
        except NoSuchElementException:
            rating = 0
            count_rating = 0
            stars = 0

        item = Info(
            name=name,
            rating=rating,
            count_rating=count_rating,
            stars=stars
        )
        return asdict(item)

    def __get_data_reviews(self) -> list:
        """Получает все отзывы пошагово"""
        reviews = []
        wait = WebDriverWait(self.driver, 10)
        
        try:
            # Ждем появления отзывов
            elements = wait.until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "business-reviews-card-view__review")
            ))
            
            if len(elements) > 1:
                # Скроллим до конца для загрузки всех отзывов
                self.__scroll_to_bottom()
                
                # Получаем обновленный список отзывов
                elements = wait.until(EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "business-reviews-card-view__review")
                ))
                
                # Обрабатываем каждый отзыв
                for i, elem in enumerate(elements):
                    try:
                        review_data = self.__get_data_item(elem)
                        if review_data:  # Проверяем, что данные не пустые
                            reviews.append(review_data)
                    except Exception as e:
                        print(f"Ошибка при обработке отзыва {i}: {e}")
                        continue
                        
        except TimeoutException:
            print("Таймаут при ожидании загрузки отзывов")
        except Exception as e:
            print(f"Ошибка при получении отзывов: {e}")
            
        return reviews

    def get_reviews_incremental(self, callback=None):
        """
        Получает отзывы пошагово, вызывая callback для каждого отзыва
        :param callback: Функция, которая будет вызвана для каждого отзыва
        :return: Количество обработанных отзывов
        """
        wait = WebDriverWait(self.driver, 10)
        processed_count = 0
        
        try:
            # Ждем появления отзывов
            elements = wait.until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "business-reviews-card-view__review")
            ))
            
            if len(elements) > 1:
                # Скроллим до конца для загрузки всех отзывов
                self.__scroll_to_bottom()
                
                # Получаем обновленный список отзывов
                elements = wait.until(EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "business-reviews-card-view__review")
                ))
                
                print(f"Найдено {len(elements)} отзывов для обработки")
                
                # Обрабатываем каждый отзыв пошагово
                for i, elem in enumerate(elements):
                    try:
                        print(f"Обрабатываем отзыв {i+1}/{len(elements)}")
                        review_data = self.__get_data_item(elem)
                        
                        if review_data and callback:
                            # Вызываем callback для сохранения отзыва
                            success = callback(review_data)
                            if success:
                                processed_count += 1
                                print(f"Отзыв {i+1} успешно сохранен")
                            else:
                                print(f"Не удалось сохранить отзыв {i+1}")
                        elif review_data:
                            processed_count += 1
                            
                    except Exception as e:
                        print(f"Ошибка при обработке отзыва {i+1}: {e}")
                        continue
                        
        except TimeoutException:
            print("Таймаут при ожидании загрузки отзывов")
        except Exception as e:
            print(f"Ошибка при получении отзывов: {e}")
            
        print(f"Всего обработано отзывов: {processed_count}")
        return processed_count

    def __isinstance_page(self):
        try:
            xpath_name = ".//h1[@class='orgpage-header-view__header']"
            name = self.driver.find_element(By.XPATH, xpath_name).text
            return True
        except NoSuchElementException:
            return False

    def parse_all_data(self) -> dict:
        """
        Начинаем парсить данные.
        :return: Словарь данных
        {
             company_info:{
                    name: str
                    rating: float
                    count_rating: int
                    stars: float
            },
            company_reviews:[
                {
                  name: str
                  icon_href: str
                  date: timestamp
                  text: str
                  stars: float
                }
            ]
        }
        """
        if not self.__isinstance_page():
            return {'error': 'Страница не найдена'}
        return {'company_info': self.__get_data_campaign(), 'company_reviews': self.__get_data_reviews()}

    def parse_reviews(self) -> dict:
        """
        Начинаем парсить данные только отзывы.
        :return: Массив отзывов
        {
            company_reviews:[
                {
                  name: str
                  icon_href: str
                  date: timestamp
                  text: str
                  stars: float
                }
            ]
        }

        """
        if not self.__isinstance_page():
            return {'error': 'Страница не найдена'}
        return {'company_reviews': self.__get_data_reviews()}

    def parse_reviews_incremental(self, callback=None) -> dict:
        """
        Парсит отзывы пошагово, вызывая callback для каждого отзыва
        :param callback: Функция для сохранения каждого отзыва
        :return: Результат парсинга
        """
        if not self.__isinstance_page():
            return {'error': 'Страница не найдена'}
        
        processed_count = self.get_reviews_incremental(callback)
        return {
            'processed_count': processed_count,
            'success': True
        }

    def parse_company_info(self) -> dict:
        """
        Начинаем парсить данные только данные о компании.
        :return: Объект компании
        {
            company_info:
                {
                    name: str
                    rating: float
                    count_rating: int
                    stars: float
                }
        }
        """
        if not self.__isinstance_page():
            return {'error': 'Страница не найдена'}
        return {'company_info': self.__get_data_campaign()}
