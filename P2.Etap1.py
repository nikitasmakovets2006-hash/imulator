import os
import sys
import json
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Исключение для ошибок конфигурации"""
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


class DependencyVisualizer:
    """Основной класс для визуализации зависимостей"""

    def __init__(self, config_path: str = "config.toml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
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

    def run(self) -> None:
        """Основной метод запуска приложения"""
        try:
            print("Загрузка конфигурации...")
            self.load_config()

            print("Конфигурация успешно загружена!")
            self.display_config()

            # Демонстрация обработки ошибок
            self.demonstrate_error_handling()

            print("\nПриложение готово к работе!")
            print("На следующем этапе будет реализована визуализация зависимостей.")

        except ConfigError as e:
            print(f"ОШИБКА КОНФИГУРАЦИИ: {e}", file=sys.stderr)
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