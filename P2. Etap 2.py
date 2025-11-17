import os
import sys
import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Set
import tempfile
import tarfile
import zipfile


class ConfigError(Exception):
    """Исключение для ошибок конфигурации"""
    pass


class DependencyError(Exception):
    """Исключение для ошибок получения зависимостей"""
    pass


class TOMLConfigParser:
    """Простой парсер TOML конфигурации"""

    @staticmethod
    def parse_toml_string(content: str) -> Dict[str, Any]:
        """Парсинг TOML из строки"""
        config = {}
        current_section = "global"
        config[current_section] = {}

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()

            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#'):
                continue

            # Обработка секций [section]
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                config[current_section] = {}
                continue

            # Обработка ключ-значение
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Преобразование значений
                try:
                    # Логические значения
                    if value.lower() == 'true':
                        parsed_value = True
                    elif value.lower() == 'false':
                        parsed_value = False
                    # Числовые значения
                    elif value.isdigit():
                        parsed_value = int(value)
                    elif value.replace('.', '').isdigit():
                        parsed_value = float(value)
                    # Строки (убираем кавычки если есть)
                    elif (value.startswith('"') and value.endswith('"')) or \
                            (value.startswith("'") and value.endswith("'")):
                        parsed_value = value[1:-1]
                    else:
                        parsed_value = value

                    config[current_section][key] = parsed_value

                except Exception as e:
                    raise ConfigError(f"Ошибка разбора строки {line_num}: {line} - {e}")

        return config

    @staticmethod
    def load_toml_file(file_path: str) -> Dict[str, Any]:
        """Загрузка и парсинг TOML файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return TOMLConfigParser.parse_toml_string(content)
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки файла {file_path}: {e}")

    @staticmethod
    def save_toml_file(config: Dict[str, Any], file_path: str) -> None:
        """Сохранение конфигурации в TOML файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for section, values in config.items():
                    if section != "global" or values:  # Пропускаем пустую глобальную секцию
                        f.write(f"[{section}]\n")
                        for key, value in values.items():
                            if isinstance(value, str):
                                f.write(f'{key} = "{value}"\n')
                            else:
                                f.write(f'{key} = {value}\n')
                    f.write('\n')
        except Exception as e:
            raise ConfigError(f"Ошибка сохранения файла {file_path}: {e}")


class PackageDependencyExtractor:
    """Класс для извлечения зависимостей Python пакетов"""

    @staticmethod
    def extract_dependencies_from_setup_py(content: str) -> List[str]:
        """Извлечение зависимостей из setup.py"""
        dependencies = []

        # Паттерны для поиска install_requires
        patterns = [
            r'install_requires\s*=\s*\[([^\]]+)\]',
            r'install_requires\s*=\s*\[(.*?)\]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                # Извлекаем зависимости из найденного списка
                dep_matches = re.findall(r'["\']([^"\']+)["\']', match)
                dependencies.extend(dep_matches)

        return list(set(dependencies))  # Убираем дубликаты

    @staticmethod
    def extract_dependencies_from_requirements(content: str) -> List[str]:
        """Извлечение зависимостей из requirements.txt"""
        dependencies = []

        for line in content.split('\n'):
            line = line.strip()

            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#'):
                continue

            # Убираем спецификаторы версий и дополнительные флаги
            package = re.split(r'[>=<!~]', line)[0].strip()
            if package and not package.startswith('-'):
                dependencies.append(package)

        return dependencies

    @staticmethod
    def extract_dependencies_from_pyproject_toml(content: str) -> List[str]:
        """Извлечение зависимостей из pyproject.toml"""
        dependencies = []

        # Поиск в секции [project] или [tool.poetry]
        patterns = [
            r'dependencies\s*=\s*\[([^\]]+)\]',
            r'requires\s*=\s*\[([^\]]+)\]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                dep_matches = re.findall(r'["\']([^"\']+)["\']', match)
                dependencies.extend(dep_matches)

        return list(set(dependencies))


class RepositoryHandler:
    """Класс для работы с репозиториями пакетов"""

    @staticmethod
    def download_and_extract_package(repo_url: str, package_name: str) -> str:
        """Скачивание и распаковка пакета из репозитория"""
        try:
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp(prefix=f"{package_name}_")

            # Определяем тип репозитория и обрабатываем
            if repo_url.startswith('https://github.com'):
                return RepositoryHandler._handle_github_repo(repo_url, temp_dir)
            elif repo_url.startswith('https://pypi.org') or 'pypi' in repo_url:
                return RepositoryHandler._handle_pypi_package(package_name, temp_dir)
            else:
                raise DependencyError(f"Неподдерживаемый тип репозитория: {repo_url}")

        except Exception as e:
            raise DependencyError(f"Ошибка загрузки пакета: {e}")

    @staticmethod
    def _handle_github_repo(repo_url: str, temp_dir: str) -> str:
        """Обработка GitHub репозитория"""
        try:
            # Преобразуем URL в архивный
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]

            archive_url = f"{repo_url}/archive/refs/heads/main.tar.gz"

            # Скачиваем архив
            archive_path = os.path.join(temp_dir, "package.tar.gz")
            urllib.request.urlretrieve(archive_url, archive_path)

            # Распаковываем
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_dir)

            # Находим распакованную директорию
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path) and item != '__pycache__':
                    return item_path

            raise DependencyError("Не удалось найти распакованные файлы пакета")

        except urllib.error.URLError as e:
            raise DependencyError(f"Ошибка загрузки с GitHub: {e}")

    @staticmethod
    def _handle_pypi_package(package_name: str, temp_dir: str) -> str:
        """Обработка пакета с PyPI"""
        try:
            # Получаем информацию о пакете через PyPI API
            api_url = f"https://pypi.org/pypi/{package_name}/json"

            with urllib.request.urlopen(api_url) as response:
                package_info = json.loads(response.read().decode())

            # Скачиваем исходный код
            download_url = None
            for url_info in package_info['urls']:
                if url_info['packagetype'] == 'sdist':
                    download_url = url_info['url']
                    break

            if not download_url:
                raise DependencyError(f"Не найден исходный код для пакета {package_name}")

            # Скачиваем и распаковываем
            download_path = os.path.join(temp_dir, "package")

            if download_url.endswith('.tar.gz'):
                download_path += '.tar.gz'
                urllib.request.urlretrieve(download_url, download_path)
                with tarfile.open(download_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
            elif download_url.endswith('.zip'):
                download_path += '.zip'
                urllib.request.urlretrieve(download_url, download_path)
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            else:
                raise DependencyError(f"Неподдерживаемый формат архива: {download_url}")

            # Находим распакованную директорию
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path) and package_name.replace('-', '_') in item:
                    return item_path

            raise DependencyError("Не удалось найти распакованные файлы пакета")

        except urllib.error.URLError as e:
            raise DependencyError(f"Ошибка загрузки с PyPI: {e}")

    @staticmethod
    def find_dependency_files(package_path: str) -> Dict[str, str]:
        """Поиск файлов с зависимостями в пакете"""
        dependency_files = {}

        for root, dirs, files in os.walk(package_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file in ['setup.py', 'requirements.txt', 'pyproject.toml']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            dependency_files[file] = f.read()
                    except UnicodeDecodeError:
                        # Пропускаем бинарные файлы
                        continue

        return dependency_files


class DependencyVisualizer:
    """Основной класс для визуализации зависимостей"""

    def __init__(self, config_path: str = "config.toml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.dependencies: List[str] = []
        self.default_config = {
            "package": {
                "name": "example-package",
                "repository_url": "https://github.com/example/repo",
                "local_repository_path": "./test-repo",
                "test_mode": False,
                "ascii_tree": True,
                "filter_substring": ""
            }
        }

    def load_config(self) -> None:
        """Загрузка конфигурации из TOML файла"""
        try:
            if not os.path.exists(self.config_path):
                self.create_default_config()
                print(f"Создан файл конфигурации по умолчанию: {self.config_path}")
                print("Пожалуйста, настройте параметры и запустите приложение снова.")
                sys.exit(0)

            self.config = TOMLConfigParser.load_toml_file(self.config_path)
            self.validate_config()

        except ConfigError as e:
            raise e
        except Exception as e:
            raise ConfigError(f"Неожиданная ошибка при загрузке конфигурации: {e}")

    def create_default_config(self) -> None:
        """Создание конфигурационного файла по умолчанию"""
        try:
            TOMLConfigParser.save_toml_file(self.default_config, self.config_path)
        except Exception as e:
            raise ConfigError(f"Не удалось создать файл конфигурации: {e}")

    def validate_config(self) -> None:
        """Валидация параметров конфигурации"""
        if 'package' not in self.config:
            raise ConfigError("Отсутствует обязательная секция 'package' в конфигурации")

        package_config = self.config['package']

        # Проверка обязательных параметров
        required_params = ['name', 'repository_url', 'local_repository_path']
        for param in required_params:
            if param not in package_config:
                raise ConfigError(f"Отсутствует обязательный параметр 'package.{param}'")

        # Валидация типов данных
        if not isinstance(package_config['name'], str):
            raise ConfigError("Параметр 'package.name' должен быть строкой")

        if not isinstance(package_config['repository_url'], str):
            raise ConfigError("Параметр 'package.repository_url' должен быть строкой")

        if not isinstance(package_config['local_repository_path'], str):
            raise ConfigError("Параметр 'package.local_repository_path' должен быть строкой")

        # Валидация логических параметров
        if 'test_mode' in package_config and not isinstance(package_config['test_mode'], bool):
            raise ConfigError("Параметр 'package.test_mode' должен быть логическим значением (true/false)")

        if 'ascii_tree' in package_config and not isinstance(package_config['ascii_tree'], bool):
            raise ConfigError("Параметр 'package.ascii_tree' должен быть логическим значением (true/false)")

        # Валидация filter_substring
        if 'filter_substring' in package_config and not isinstance(package_config['filter_substring'], str):
            raise ConfigError("Параметр 'package.filter_substring' должен быть строкой")

        # Проверка конфликтующих параметров
        if package_config.get('test_mode', False):
            local_path = package_config['local_repository_path']
            if not os.path.exists(local_path):
                raise ConfigError(f"Тестовый репозиторий не найден: {local_path}")

    def display_config(self) -> None:
        """Вывод всех параметров конфигурации в формате ключ-значение"""
        print("=" * 50)
        print("НАСТРОЙКИ ПРИЛОЖЕНИЯ")
        print("=" * 50)

        package_config = self.config.get('package', {})

        for key, value in package_config.items():
            print(f"{key:25} : {value}")

        print("=" * 50)

    def demonstrate_error_handling(self) -> None:
        """Демонстрация обработки ошибок для всех параметров"""
        test_cases = [
            # (параметр, неверное значение, ожидаемая ошибка)
            ("name", 123, "Параметр 'package.name' должен быть строкой"),
            ("repository_url", None, "Параметр 'package.repository_url' должен быть строкой"),
            ("test_mode", "not_a_bool", "Параметр 'package.test_mode' должен быть логическим значением"),
            ("ascii_tree", 0, "Параметр 'package.ascii_tree' должен быть логическим значением"),
            ("filter_substring", [], "Параметр 'package.filter_substring' должен быть строкой"),
        ]

        print("\nДЕМОНСТРАЦИЯ ОБРАБОТКИ ОШИБОК")
        print("=" * 50)

        for param, wrong_value, expected_error in test_cases:
            print(f"Тест параметра '{param}':")
            print(f"  Неверное значение: {wrong_value} ({type(wrong_value).__name__})")
            print(f"  Ожидаемая ошибка: {expected_error}")
            print()

    def get_dependencies(self) -> None:
        """Получение прямых зависимостей пакета"""
        try:
            package_config = self.config['package']
            package_name = package_config['name']
            repo_url = package_config['repository_url']
            test_mode = package_config.get('test_mode', False)
            filter_substring = package_config.get('filter_substring', '')

            print(f"\nАнализ зависимостей пакета: {package_name}")
            print("=" * 50)

            if test_mode:
                # Режим тестирования с локальным репозиторием
                local_path = package_config['local_repository_path']
                print(f"Режим тестирования: использование локального пути {local_path}")
                dependency_files = RepositoryHandler.find_dependency_files(local_path)
            else:
                # Режим работы с удаленным репозиторием
                print(f"Загрузка пакета из: {repo_url}")
                package_path = RepositoryHandler.download_and_extract_package(repo_url, package_name)
                dependency_files = RepositoryHandler.find_dependency_files(package_path)

            # Анализ найденных файлов с зависимостями
            all_dependencies = set()

            for file_name, content in dependency_files.items():
                print(f"Найден файл: {file_name}")

                if file_name == 'setup.py':
                    deps = PackageDependencyExtractor.extract_dependencies_from_setup_py(content)
                elif file_name == 'requirements.txt':
                    deps = PackageDependencyExtractor.extract_dependencies_from_requirements(content)
                elif file_name == 'pyproject.toml':
                    deps = PackageDependencyExtractor.extract_dependencies_from_pyproject_toml(content)
                else:
                    deps = []

                all_dependencies.update(deps)
                print(f"  Найдено зависимостей: {len(deps)}")

            # Применяем фильтрацию если задана
            if filter_substring:
                filtered_deps = [dep for dep in all_dependencies if filter_substring in dep]
                print(f"\nПрименен фильтр: '{filter_substring}'")
                print(f"Зависимостей после фильтрации: {len(filtered_deps)}")
                self.dependencies = sorted(filtered_deps)
            else:
                self.dependencies = sorted(all_dependencies)

        except DependencyError as e:
            raise e
        except Exception as e:
            raise DependencyError(f"Неожиданная ошибка при получении зависимостей: {e}")

    def display_dependencies(self) -> None:
        """Вывод прямых зависимостей пакета"""
        if not self.dependencies:
            print("Прямые зависимости не найдены.")
            return

        print(f"\nПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА ({len(self.dependencies)}):")
        print("=" * 50)

        for i, dependency in enumerate(self.dependencies, 1):
            print(f"{i:2}. {dependency}")

    def run(self) -> None:
        """Основной метод запуска приложения"""
        try:
            print("Загрузка конфигурации...")
            self.load_config()

            print("Конфигурация успешно загружена!")
            self.display_config()

            # Демонстрация обработки ошибок
            self.demonstrate_error_handling()

            # Получение и отображение зависимостей
            self.get_dependencies()
            self.display_dependencies()

            print("\nЭтап 2 завершен успешно!")
            print("Собраны данные о прямых зависимостях пакета.")

        except (ConfigError, DependencyError) as e:
            print(f"ОШИБКА: {e}", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nПриложение прервано пользователем.")
            sys.exit(0)
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """Точка входа в приложение"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.toml"

    app = DependencyVisualizer(config_path)
    app.run()


if __name__ == "__main__":
    main()