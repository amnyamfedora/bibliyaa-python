#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("[*] Инициализация системы...")
import requests
import re
import time
import random
from colorama import init, Fore
import os
import sys
import json
import hashlib
import threading
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime
import traceback
import inspect
import random
from private import PrivateMethod
import urllib3
try:
   import html
   html_available = True
except ImportError:
   html_available = False
try:
   import chardet
   have_chardet = True
except ImportError:
   have_chardet = False
if sys.gettrace() is not None:
  __debugable__ = True
else:
   __debugable__ = False
__debugable__ = True
print("[*] Настройка логирования...")
if __debugable__:
   logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
   logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
print("Инициализация цветового вывода...")
init(autoreset=True)
def __bug_on__(e):
   """ Function for a fatal exceptions.Only if impossible to continue work/recovery without data corruption or incorrect working """
   print(f"Fatal:{e}")
   if __debugable__: traceback.print_exc()
   exit(1)
@dataclass
class JokeConfig:
    min_russian_letters: int = 35
    request_timeout: int = 20
    min_joke_length: int = 40
    max_joke_length: int = 600
    shown_file: str = "shown_jokes.json"
    unseen_file: str = "unseen_jokes.json"
    background_parsing_interval: int = 2

class JokeProcessor:
    def __init__(self, config: Optional[JokeConfig] = None):
        self.config = config or JokeConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })

        self.joke_sources = [
            "https://www.anekdot.ru/last/anekdot/",
            "https://www.anekdot.ru/random/anekdot/",
        ]
        self.encodings = ['utf-8', 'windows-1251', 'cp1251']

        # Инициализация JSON-файлов
        self.init_json_files()
        self.delay = False
        self.time_delay = 0.09
        self.file_lock = threading.Lock()
        self.parsing_active = True
        # Фоновый парсинг (работает с теми же файлами, блокировки через threading.Lock)

    def init_json_files(self):
        """Создаёт JSON-файлы если их нет"""
        for filepath in [self.config.shown_file, self.config.unseen_file]:
            logger.debug(f"init_jdon_files: filepath {filepath}")
            if not os.path.exists(filepath):
                logger.debug(f"creating file {filepath}.")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(Fore.GREEN + f"✓ Создан файл: {filepath}")

    def load_json(self, filepath: str) -> Dict:
        """Безопасная загрузка JSON с блокировкой"""
        with self.file_lock:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Warning: exception {e} while loading json.falling back to {'{}'}(MAY CORRUPT PROGRAMM!!!)")
                return {}

    def save_json(self, filepath: str, data: Dict):
        """Безопасное сохранение JSON с блокировкой"""
        with self.file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def get_joke_hash(self, joke_text: str) -> str:
        logger.debug(f"get_joke_hash called with joke_text={joke_text}")
        normalized = re.sub(r'\s+', ' ', joke_text.strip().lower())
        logger.debug(f"Normalized joke: {normalized}")
        hash = hashlib.md5(normalized.encode('utf-8')).hexdigest()
        logger.debug(f"{joke_text} hash: {hash}")
        return hash

    def is_joke_shown(self, joke_hash: str) -> bool:
        logger.debug(f"is_joke_shown called with joke_hash={joke_hash}")
        shown_data = self.load_json(self.config.shown_file)
        result = (joke_hash in shown_data)
        logger.debug(f"result {result}")
        return result
    def is_joke_in_unseen(self, joke_hash: str) -> bool:
        logger.debug(f"is_joke_in_unseen called with joke_hash={joke_hash}")
        unseen_data = self.load_json(self.config.unseen_file)
        return joke_hash in unseen_data

    def mark_joke_as_shown(self, joke_text: str, source_url: str = None):
        joke_hash = self.get_joke_hash(joke_text)
        shown_data = self.load_json(self.config.shown_file)

        if joke_hash in shown_data:
            shown_data[joke_hash]['used_count'] += 1
        else:
            shown_data[joke_hash] = {
                'text': joke_text,
                'source_url': source_url,
                'length': len(joke_text),
                'added_date': datetime.now().isoformat(),
                'used_count': 1
            }
        self.save_json(self.config.shown_file, shown_data)
        print(Fore.GREEN + f"✓ Анекдот добавлен в показанные (хеш: {joke_hash[:8]}...)")

    def add_to_unseen(self, joke_text: str, source_url: str = None) -> bool:
        joke_hash = self.get_joke_hash(joke_text)
        if self.is_joke_shown(joke_hash):
            return False
        if self.is_joke_in_unseen(joke_hash):
            return False

        unseen_data = self.load_json(self.config.unseen_file)
        unseen_data[joke_hash] = {
            'text': joke_text,
            'source_url': source_url,
            'added_date': datetime.now().isoformat()
        }
        self.save_json(self.config.unseen_file, unseen_data)
        return True

    def get_unseen_joke_from_db(self) -> Optional[str]:
        """Извлекает случайный непоказанный анекдот"""
        logger.debug("get_unseen_joke_from_db called!")
        unseen_data = self.load_json(self.config.unseen_file)
        if not unseen_data:
            return None

        # Выбираем случайный
        joke_hash = random.choice(list(unseen_data.keys()))
        joke_info = unseen_data[joke_hash]
        joke_text = joke_info['text']
        source_url = joke_info['source_url']

        # Удаляем из unseen и добавляем в shown
        del unseen_data[joke_hash]
        self.save_json(self.config.unseen_file, unseen_data)
        self.mark_joke_as_shown(joke_text, source_url)

        return joke_text

    def get_database_stats(self) -> dict:
        logger.debug("get_database_stats called.")
        shown_data = self.load_json(self.config.shown_file)
        unseen_data = self.load_json(self.config.unseen_file)
        total_shown = len(shown_data)
        total_unseen = len(unseen_data)
        total_uses = sum(item.get('used_count', 0) for item in shown_data.values())

        shown_size = os.path.getsize(self.config.shown_file) / (1024 * 1024) if os.path.exists(self.config.shown_file) else 0
        unseen_size = os.path.getsize(self.config.unseen_file) / (1024 * 1024) if os.path.exists(self.config.unseen_file) else 0

        stats = {
            'total_shown': total_shown,
            'total_unseen': total_unseen,
            'total_uses': total_uses,
            'shown_db_mb': shown_size,
            'unseen_db_mb': unseen_size,
            'total_db_mb': shown_size + unseen_size
        }
        logger.debug(f"[get_database_stats] stats:{stats}.")
        return stats
    @PrivateMethod
    def clear_terminal(self):
        logger.debug(f"clear_terminal called")
        if not __debugable__:os.system('cls' if os.name == 'nt' else 'clear')

    def type_effect(self, text: str, delay: float = 0.02):
        logger.debug(f"type_effect called with text={text}, delay={delay}")
        for char in text:
            print(char, end='', flush=True)
            if self.delay:time.sleep(self.time_delay * random.uniform(0.8, 1.2))
        print()

    def is_valid_russian_text(self, text: str) -> bool:
        logger.debug(f"is_valid_russian_text called with text={text}")
        if not text or len(text) < self.config.min_russian_letters:
            return False
        logger.debug(f"[is_valid_russian_text](1/4)checks passed:  not text or len(text) check passed.")
        russian_letters = sum(1 for char in text if 'а' <= char <= 'я' or 'А' <= char <= 'Я' or char in 'ёЁ')
        if russian_letters < self.config.min_russian_letters:
            return False
        logger.debug(f"russian_letters = {russian_letters}")
        logger.debug(f"[is_valid_russian_text] (2/4) checks passed: if russian_letters < self.config.min_russian_letters check passed. ")


        tech_patterns = ['function', 'var ', 'const ', 'let ', 'import ',
                         'http://', 'https://', 'www.', '.com', '.ru', '.org',
                         'css', 'html', 'body', 'div', 'span', 'href=']
        logger.debug(f"[is_valid_russian_text] tech_patterns = {tech_patterns}.")
        if any(pattern in text.lower() for pattern in tech_patterns):
           return False
        logger.debug(f"[is_valid_russian_text](3/4)checks passed:  any(pattern in text.lower() for pattern in tech_patterns) check passed.")
        logger.debug(f"[is_valid_russian_text] self.config.min_joke_length = {self.config.min_joke_length}")

        logger.debug(f"[is_valid_russian_text] [4/4) all checks passed.")
        return True

    def clean_text(self, text: str) -> str:
        logger.debug(f"clean_text called with text={text}")
        text = re.sub(r'<[^>]+>', '', text)
        if html_available:
            text = html.unescape(text)
            logger.debug("clean_text: optional requirement html is available")
        text = re.sub(r'<br\s*/?>', '\n', text)
        logger.debug(f"[clean_text] Text after 1 re.sub: {text}")
        text = re.sub(r'\n\s*\n', '\n', text)
        logger.debug(f"[clean_text] text after 2 re.sub: {text}")
        logger.debug(f"[clean_text] text after .strip:{text.strip()}")
        return text.strip()

    def detect_encoding(self, content: bytes) -> str:
        logger.debug(f"detect_encoding called with content={content}")
        if have_chardet:
            result = chardet.detect(content)
            logger.debug(f"result = {result}")
            if result['confidence'] > 0.7:
                return result['encoding']
            else: logger.debug(f"Chardet confidence smaller then 0.7.")
        else:
            logger.debug("[detect_encoding]No chardet, falling back to mannualy detecting")
        for encoding in self.encodings:
                logger.debug(f"Trying: encoding {encoding}")
                try:
                   content.decode(encoding)
                except Exception as e:logger.debug(f"[detect_encoding] Exception {e} at content.decode(Is it normal?)")
                logger.debug(f"success, encoding is {encoding}")
                return encoding
        logger.debug("Unable to define content encoding.Falling back to utf-8")
        return 'utf-8'

    def extract_jokes(self, html_content: str) -> List[str]:
        logger.debug(f"extract_jokes called with html_content={html_content}")
        jokes = []
        pattern = r'<div class="topicbox" data-t="j"[^>]*>.*?<div class="text">(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        logger.debug(f"matches: {matches}, pattern={pattern}")
        for match in matches:
            logger.debug("[extract_jokes] handling {match}...")
            cleaned = self.clean_text(match)
            logger.debug(f"[extract_jokes] cleaned: {cleaned}")
            if len(cleaned) >= 30 and not cleaned.startswith('Анекдоты:'):
                logger.debug(f"Found valid joke: {cleaned}")
                jokes.append(cleaned)
            else:
               logger.debug(f"Joke is not match with filter:{cleaned}.May our filter bad or good.")
        if not jokes:
            logger.debug("FALLING BACK To old pattern: New pattern not found jokes.")
            old_patterns = [
                r'<div[^>]*class="text"[^>]*>(.*?)</div>',
                r'<p[^>]*>(.*?)</p>',
            ] # TODO: add debug logic to this(Like in new patterns handling)
            for pattern in old_patterns:
                try:
                    found = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                    for joke in found:
                        if isinstance(joke, tuple):
                            joke = joke[0]
                        cleaned = self.clean_text(joke)
                        if 40 <= len(cleaned) <= 600 and not cleaned.startswith('Анекдоты:'):
                            jokes.append(cleaned)
                except:
                    continue
        return jokes

    def get_unique_joke_online(self, source_url: str) -> Optional[str]:
        try:
            response = self.session.get(source_url, timeout=self.config.request_timeout)
            logger.debug(f"[get_unique_joke_online), Source url: {source_url}, response: {response}.")
            encoding = self.detect_encoding(response.content)
            logger.debug(f"[get_unique_joke_online] encoding: {encoding}.")
            response.encoding = encoding
            if response.status_code != 200:
                logger.error("[get_unique_joke_online] Status code != 200")
                logger.debug(f"[get_unique_joke_online] status code: {response.status_code}")
                return None
            jokes = self.extract_jokes(response.text)
            logger.debug(f"[get_unique_joke_online] Jokes: {jokes}.")
            valid_jokes = []
            for joke in jokes:
                if self.is_valid_russian_text(joke):
                    joke_hash = self.get_joke_hash(joke)
                    if not self.is_joke_shown(joke_hash):
                        valid_jokes.append(joke)
            if valid_jokes:
                valid_jokes.sort(key=len, reverse=True)
                selected_joke = valid_jokes[0]
                logger.debug(f"[get_unique_joke_online] selected joke: {selected_joke}")
                self.mark_joke_as_shown(selected_joke, source_url)
                return selected_joke
        except Exception as e:
            logger.error(f"Ошибка при получении анекдота: {e}")
            return None
        logger.debug(f"[get_unique_joke_online] No 'suitable' jokes found.")
        return None

    def parse_and_store_unseen(self):
        """Фоновый парсинг — сохраняет новые анекдоты в unseen"""
        logger.debug("[parse_and_store_unseen] called.")
        for source in self.joke_sources:
            try:
                logger.debug(f"[parse_and_store_unseen] self.joke_sources:{self.joke_sources}, source:{source}.starying session.")
                response = self.session.get(source, timeout=self.config.request_timeout)
                logger.debug(f"response code:{response}.")
                encoding = self.detect_encoding(response.content)
                response.encoding = encoding
                if response.status_code != 200:
                    continue# already logged.
                jokes = self.extract_jokes(response.text)
                for joke in jokes:
                    if self.is_valid_russian_text(joke):
                        self.add_to_unseen(joke, source)
            except Exception as e:
               logger.debug(f"Fatal exception in parse_and_store_unseen: {e}.")
               # Bug on is no needed here



    def _background_worker(self):
        logger.debug(f"background worker called.parsing active:{self.parsing_active}.self.config.background_parsing_interval:{self.config.background_parsing_interval}")
        while self.parsing_active:
            try:
                self.parse_and_store_unseen()
            except Exception as e:
                logger.error(f"Ошибка в фоновом потоке: {e}")
            time.sleep(self.config.background_parsing_interval)

    def print_joke(self, joke: str, number: int):
        colors = [(Fore.GREEN, Fore.YELLOW), (Fore.CYAN, Fore.MAGENTA),
                  (Fore.YELLOW, Fore.BLUE), (Fore.MAGENTA, Fore.CYAN)]
        border_color, text_color = random.choice(colors)
        print(border_color + "┌─────────────────────────────────────────────────────┐")
        print(f"{border_color}│{text_color}               АНЕКДОТ #{number:02d}                  {border_color}│")
        print(border_color + "└─────────────────────────────────────────────────────┘")
        print()
        print(text_color, end='')
        self.type_effect(joke, 0.03)
        print()
        print(border_color + "─" * 55)
        print()
    def is_internet_available(self) -> bool:
        logger.debug("is_internet_available called.")
        try:
            requests.head("https://www.anekdot.ru", timeout=5)
            return True
        except requests.exceptions.ReadTimeout as e:
            logger.debug(f"[is_internet_available] requests.exceptions.ReadTimeout: {e}.not a fatal exception.")
            return False
        except urllib3.exceptions.ConnectTimeoutError:
           logger.debug("No internet, catched urllib3.exceptions.ConnectTimeoutError")
           return False
        except TimeoutError:
           logger.debug("[is_internet_available] No internet, catched TimeOutError")
           return False
        except ConnectionResetError:
           logger.debug("[is_internet_available] No internet, connection killed force by RST")
           return False
        except PermissionError as e:
           logger.debug(f"[is_internet_available] Permission Error: {e}!")
           return False
        except urllib3.exceptions.MaxRetryError:
           logger.debug("urllib3.exceptions.MaxRetryError!")
           if __debugable__: traceback.print_exc()
           return False
        except requests.exceptions.ConnectTimeout:
            logger.debug(f"Connection Timeout!")
            return False
        except ConnectionRefusedError:
           logger.debug(f"[is_internet_available] Connection refused")
           return False
        except Exception as e:
            logger.debug(f"[is_internet_available] {e}")
            if __debugable__:traceback.print_exc()
            return False
    @PrivateMethod
    def __run_thread(self):
         # Фоновый парсинг (работает с теми же файлами, блокировки через threading.Lock)
        self.file_lock = threading.Lock()
        self.background_thread = threading.Thread(target=self._background_worker, daemon=True)
        self.background_thread.start()
        print(Fore.GREEN + "[*] Фоновый парсинг анекдотов запущен")

    def run_session(self):
        self.clear_terminal()
        print(Fore.GREEN + "=" * 60)
        print(Fore.YELLOW + "       СИСТЕМА ПОИСКА АНЕКДОТОВ v3.0 (JSON)")
        print(Fore.GREEN + "=" * 60)
        print()
        stats = self.get_database_stats()
        print(Fore.CYAN + f"📊 Показано: {stats['total_shown']} | В резерве: {stats['total_unseen']}")
        print(Fore.MAGENTA + f"💾 БД показанных: {stats['shown_db_mb']:.2f} MB | Резерв: {stats['unseen_db_mb']:.2f} MB")
        print()
        internet_ok = self.is_internet_available()

        if internet_ok:self.__run_thread() # только если есть интернет

        successful = 0
        target = 5

        if __debugable__:
            logger.info("Режим разработчика включен")
        if not internet_ok:
           self.parsing_active = False # Вырубаем парсинг чтобы не зашумлять логи 'fatal exception in  thread'⚡🤦‍♀️, иначе ни пользователю ни разработчику этот мусор не будет нужен
           logger.warning("фоновый парсинг выключен потому что программа не отлаживается и нет интернета, чтобы не шуметь в логах.")
        for i in range(1, target + 1):
            joke = None
            if internet_ok:
                for source in self.joke_sources:
                    joke = self.get_unique_joke_online(source)
                    if joke:
                        break
            if not joke:
                joke = self.get_unseen_joke_from_db()
                if joke:
                    if not internet_ok:
                        print(Fore.YELLOW + "⚠ РЕЖИМ РЕЗЕРВА: интернет отключён, показываем из базы")
                    else:
                        print(Fore.YELLOW + "⚠ РЕЖИМ РЕЗЕРВА: нет новых анекдотов в сети")
                    self.print_joke(joke, i)
                    successful += 1
                else:
                    print(Fore.RED + f"⚠ Не удалось найти анекдот #{i}: нет интернета и база резерва пуста")
            else:
                self.print_joke(joke, i)
                successful += 1

            if i < target:
                time.sleep(1)

        print(Fore.GREEN + "=" * 60)
        print(Fore.YELLOW + f"       ЗАВЕРШЕНО. НАЙДЕНО: {successful}/{target}")
        final_stats = self.get_database_stats()
        print(Fore.CYAN + f"📈 Показано всего: {final_stats['total_shown']} | В резерве: {final_stats['total_unseen']}")
        print(Fore.GREEN + "=" * 60)

def main():
    processor = None
    try:
        processor = JokeProcessor()

        while True:
            processor.run_session()
            print(Fore.CYAN + "\nНажмите Enter для нового поиска или Ctrl+C для выхода...")
            input()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\nЗавершение работы.")
        if processor:
            processor.parsing_active = False
    except Exception as e:
        print(Fore.RED + f"\nОшибка: {e}")
        __bug_on__(e)

if __name__ == "__main__":

    main()
