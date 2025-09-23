import csv
import xml.etree.ElementTree as ET
import re
from difflib import SequenceMatcher
from decimal import Decimal


class ImprovedProductMatcher:
    """
    Улучшенная система сопоставления товаров между XML и CSV файлами
    """
    
    def __init__(self):
        self.csv_data = {}
        self.xml_data = {}
        self.match_cache = {}
    
    def load_csv_data(self, csv_file_path):
        """Загружает данные из CSV файла"""
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            headers = [h.strip().replace('\ufeff', '') for h in headers]
            
            for row in reader:
                if len(row) > 3 and row[3].strip():
                    product_name = row[3].strip()
                    self.csv_data[product_name] = {
                        'id': row[0],
                        'name': product_name,
                        'price': row[25] if len(row) > 25 else '',
                        'categories': row[26] if len(row) > 26 else '',
                        'sku': row[2] if len(row) > 2 else '',
                        'tags': row[27] if len(row) > 27 else '',
                        'description': row[8] if len(row) > 8 else '',
                        'short_description': row[7] if len(row) > 7 else ''
                    }
    
    def load_xml_data(self, xml_file_path):
        """Загружает данные из XML файла"""
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        for item in root.findall('.//item'):
            post_type_elem = item.find('.//{http://wordpress.org/export/1.2/}post_type')
            if post_type_elem is not None and post_type_elem.text == 'product':
                title_elem = item.find('title')
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    
                    # Извлекаем цену
                    meta_data = {}
                    for meta in item.findall('.//{http://wordpress.org/export/1.2/}postmeta'):
                        key_elem = meta.find('{http://wordpress.org/export/1.2/}meta_key')
                        value_elem = meta.find('{http://wordpress.org/export/1.2/}meta_value')
                        if key_elem is not None and value_elem is not None:
                            meta_data[key_elem.text] = value_elem.text
                    
                    price = None
                    for key in ['_regular_price', '_price', '_sale_price']:
                        if key in meta_data and meta_data[key]:
                            try:
                                price = Decimal(meta_data[key].replace(',', '.'))
                                break
                            except:
                                continue
                    
                    # Извлекаем категории
                    categories = []
                    for category in item.findall('category'):
                        domain = category.get('domain', '')
                        text = category.text if category.text else ''
                        if domain == 'product_cat' and text:
                            categories.append(text)
                    
                    # Извлекаем атрибуты
                    attributes = []
                    for category in item.findall('category'):
                        domain = category.get('domain', '')
                        text = category.text if category.text else ''
                        if domain.startswith('pa_') and text:
                            attributes.append({
                                'domain': domain,
                                'value': text
                            })
                    
                    self.xml_data[title] = {
                        'name': title,
                        'price': price,
                        'categories': categories,
                        'attributes': attributes,
                        'meta_data': meta_data
                    }
    
    def normalize_name(self, name):
        """Нормализует название для сравнения"""
        if not name:
            return ''
        # Убираем лишние пробелы и приводим к нижнему регистру
        name = re.sub(r'\s+', ' ', name.strip().lower())
        # Убираем знаки препинания
        name = re.sub(r'[^\w\s]', '', name)
        return name
    
    def calculate_name_similarity(self, name1, name2):
        """Вычисляет схожесть названий (0-1)"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if not norm1 or not norm2:
            return 0
        
        # Точное совпадение
        if norm1 == norm2:
            return 1.0
        
        # Схожесть по словам
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        word_similarity = len(intersection) / len(union) if union else 0
        
        # Схожесть по символам
        char_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Комбинированная схожесть
        combined_similarity = (word_similarity * 0.7 + char_similarity * 0.3)
        
        return combined_similarity
    
    def calculate_price_similarity(self, price1, price2):
        """Вычисляет схожесть цен (0-1)"""
        if not price1 or not price2:
            return 0
        
        try:
            p1 = float(price1) if isinstance(price1, (int, float, Decimal)) else float(price1)
            p2 = float(price2) if isinstance(price2, (int, float, Decimal)) else float(price2)
            
            if p1 == 0 and p2 == 0:
                return 1.0
            
            if p1 == 0 or p2 == 0:
                return 0
            
            # Относительная разница
            diff = abs(p1 - p2) / max(p1, p2)
            return max(0, 1 - diff)
        except:
            return 0
    
    def calculate_category_similarity(self, categories1, categories2):
        """Вычисляет схожесть категорий (0-1)"""
        if not categories1 or not categories2:
            return 0
        
        # Нормализуем категории
        norm_cats1 = set(self.normalize_name(cat) for cat in categories1)
        norm_cats2 = set()
        
        for cat in categories2:
            if isinstance(cat, str):
                # Парсим категории из CSV (разделены запятыми и >)
                for subcat in cat.split(','):
                    subcat = subcat.strip()
                    if '>' in subcat:
                        # Иерархические категории
                        parts = subcat.split('>')
                        for part in parts:
                            norm_cats2.add(self.normalize_name(part.strip()))
                    else:
                        norm_cats2.add(self.normalize_name(subcat))
        
        if not norm_cats1 or not norm_cats2:
            return 0
        
        intersection = norm_cats1.intersection(norm_cats2)
        union = norm_cats1.union(norm_cats2)
        
        return len(intersection) / len(union) if union else 0
    
    def calculate_overall_similarity(self, xml_item, csv_item):
        """Вычисляет общую схожесть товаров"""
        # Схожесть названий (основной критерий)
        name_sim = self.calculate_name_similarity(xml_item['name'], csv_item['name'])
        
        # Схожесть цен
        price_sim = self.calculate_price_similarity(xml_item.get('price'), csv_item.get('price'))
        
        # Схожесть категорий
        category_sim = self.calculate_category_similarity(
            xml_item.get('categories', []), 
            [csv_item.get('categories', '')]
        )
        
        # Взвешенная схожесть
        overall_sim = (
            name_sim * 0.6 +      # Название - основной критерий
            price_sim * 0.25 +    # Цена - важный критерий
            category_sim * 0.15   # Категории - дополнительный критерий
        )
        
        return {
            'overall': overall_sim,
            'name': name_sim,
            'price': price_sim,
            'category': category_sim
        }
    
    def find_best_match(self, xml_name, threshold=0.7):
        """Находит лучшее совпадение для XML товара в CSV"""
        if xml_name not in self.xml_data:
            return None
        
        xml_item = self.xml_data[xml_name]
        best_match = None
        best_score = 0
        
        for csv_name, csv_item in self.csv_data.items():
            similarity = self.calculate_overall_similarity(xml_item, csv_item)
            
            if similarity['overall'] >= threshold and similarity['overall'] > best_score:
                best_match = {
                    'csv_name': csv_name,
                    'csv_item': csv_item,
                    'similarity': similarity
                }
                best_score = similarity['overall']
        
        return best_match
    
    def find_all_matches(self, xml_name, threshold=0.5):
        """Находит все совпадения для XML товара в CSV"""
        if xml_name not in self.xml_data:
            return []
        
        xml_item = self.xml_data[xml_name]
        matches = []
        
        for csv_name, csv_item in self.csv_data.items():
            similarity = self.calculate_overall_similarity(xml_item, csv_item)
            
            if similarity['overall'] >= threshold:
                matches.append({
                    'csv_name': csv_name,
                    'csv_item': csv_item,
                    'similarity': similarity
                })
        
        # Сортируем по общей схожести
        matches.sort(key=lambda x: x['similarity']['overall'], reverse=True)
        return matches
    
    def get_statistics(self):
        """Возвращает статистику сопоставления"""
        total_xml = len(self.xml_data)
        total_csv = len(self.csv_data)
        
        exact_matches = 0
        good_matches = 0
        partial_matches = 0
        no_matches = 0
        
        for xml_name in self.xml_data.keys():
            best_match = self.find_best_match(xml_name, threshold=0.5)
            if best_match:
                score = best_match['similarity']['overall']
                if score >= 0.95:
                    exact_matches += 1
                elif score >= 0.8:
                    good_matches += 1
                else:
                    partial_matches += 1
            else:
                no_matches += 1
        
        return {
            'total_xml': total_xml,
            'total_csv': total_csv,
            'exact_matches': exact_matches,
            'good_matches': good_matches,
            'partial_matches': partial_matches,
            'no_matches': no_matches,
            'match_rate': (exact_matches + good_matches + partial_matches) / total_xml * 100 if total_xml > 0 else 0
        }


# Пример использования
if __name__ == "__main__":
    matcher = ImprovedProductMatcher()
    
    # Загружаем данные
    matcher.load_csv_data('/app/wc-product.csv')
    matcher.load_xml_data('/app/topcvetok_xml.xml')
    
    # Получаем статистику
    stats = matcher.get_statistics()
    print("Статистика сопоставления:")
    print(f"XML товаров: {stats['total_xml']}")
    print(f"CSV товаров: {stats['total_csv']}")
    print(f"Точные совпадения (>=0.95): {stats['exact_matches']}")
    print(f"Хорошие совпадения (0.8-0.95): {stats['good_matches']}")
    print(f"Частичные совпадения (0.5-0.8): {stats['partial_matches']}")
    print(f"Без совпадений (<0.5): {stats['no_matches']}")
    print(f"Процент сопоставления: {stats['match_rate']:.1f}%")
    
    # Тестируем на примерах
    print("\nПримеры сопоставления:")
    test_names = list(matcher.xml_data.keys())[:5]
    for xml_name in test_names:
        best_match = matcher.find_best_match(xml_name)
        if best_match:
            print(f"\nXML: {xml_name}")
            print(f"CSV: {best_match['csv_name']}")
            print(f"Схожесть: {best_match['similarity']['overall']:.3f}")
            print(f"  - Название: {best_match['similarity']['name']:.3f}")
            print(f"  - Цена: {best_match['similarity']['price']:.3f}")
            print(f"  - Категории: {best_match['similarity']['category']:.3f}")
