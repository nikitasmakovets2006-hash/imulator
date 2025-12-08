import sys
import json
import re
from typing import Any, Dict, List, Optional

class ConfigParser:
    def __init__(self):
        self.vars = {}
        self.pos = 0
        self.text = ""

    def parse(self, input_text: str) -> Dict[str, Any]:
        """Основной метод парсинга"""
        self.text = input_text
        self.pos = 0
        self.vars = {}
        result = {}

        while self.pos < len(self.text):
            self.skip_whitespace()

            if self.pos >= len(self.text):
                break

            # Обработка объявления переменной
            if self.text.startswith('var ', self.pos):
                self.pos += 4
                self.parse_var_declaration()
            # Обработка ключ-значение
            else:
                key = self.parse_name()
                self.skip_whitespace()

                if self.peek() == '=':
                    self.pos += 1
                    self.skip_whitespace()
                    value = self.parse_value()
                    result[key] = value

        return result

    def parse_var_declaration(self):
        """Парсинг объявления переменной var имя значение"""
        self.skip_whitespace()
        name = self.parse_name()
        self.skip_whitespace()
        value = self.parse_value()
        self.vars[name] = value

        # Пропускаем возможную точку с запятой
        self.skip_whitespace()
        if self.peek() == ';':
            self.pos += 1

    def parse_value(self) -> Any:
        """Парсинг значения любого типа"""
        char = self.peek()

        if char == '"':
            return self.parse_string()
        elif char == '[':
            return self.parse_array()
        elif char == '@':
            return self.parse_expression()
        elif char == '-' or char.isdigit() or char == '.':
            return self.parse_number()
        elif char.isalpha():
            # Это может быть имя переменной или специальное значение
            name = self.parse_name()
            if name in self.vars:
                return self.vars[name]
            raise SyntaxError(f"Неизвестная переменная: {name}")
        else:
            raise SyntaxError(f"Неожиданный символ: {char}")

    def parse_string(self) -> str:
        """Парсинг строк в кавычках"""
        self.pos += 1  # Пропускаем открывающую кавычку
        start_pos = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            self.pos += 1

        if self.pos >= len(self.text):
            raise SyntaxError("Незакрытая строка")

        result = self.text[start_pos:self.pos]
        self.pos += 1  # Пропускаем закрывающую кавычку
        return result

    def parse_number(self):
        """Парсинг чисел"""
        pattern = r'-?(\d+|\d+\.\d*|\.\d+)([eE][-+]?\d+)?'
        match = re.match(pattern, self.text[self.pos:])

        if not match:
            raise SyntaxError(f"Ошибка в числе на позиции {self.pos}")

        num_str = match.group(0)
        self.pos += len(num_str)

        # Пробуем преобразовать в int или float
        if '.' in num_str or 'e' in num_str.lower():
            return float(num_str)
        return int(num_str)

    def parse_array(self) -> List[Any]:
        """Парсинг массивов [значение; значение; ...]"""
        self.pos += 1  # Пропускаем '['
        result = []

        while True:
            self.skip_whitespace()

            if self.peek() == ']':
                self.pos += 1
                break

            value = self.parse_value()
            result.append(value)

            self.skip_whitespace()

            if self.peek() == ';':
                self.pos += 1
            elif self.peek() == ']':
                continue
            else:
                raise SyntaxError(f"Ожидалось ';' или ']' на позиции {self.pos}")

        return result

    def parse_expression(self) -> Any:
        """Парсинг выражений @{операция аргументы}"""
        if not self.text.startswith('@{', self.pos):
            raise SyntaxError(f"Ожидалось выражение @{{ на позиции {self.pos}")

        self.pos += 2  # Пропускаем '@{'
        self.skip_whitespace()

        # Определяем операцию
        op = self.parse_name()
        self.skip_whitespace()

        # Собираем аргументы
        args = []
        while self.peek() != '}':
            arg = self.parse_value()
            args.append(arg)
            self.skip_whitespace()

        self.pos += 1  # Пропускаем '}'

        # Выполняем операцию
        return self.evaluate_expression(op, args)

    def evaluate_expression(self, op: str, args: List[Any]) -> Any:
        """Вычисление выражения"""
        if op == '+':
            if len(args) != 2:
                raise SyntaxError(f"Операция + требует 2 аргумента")
            return args[0] + args[1]
        elif op == '-':
            if len(args) != 2:
                raise SyntaxError(f"Операция - требует 2 аргумента")
            return args[0] - args[1]
        elif op == '*':
            if len(args) != 2:
                raise SyntaxError(f"Операция * требует 2 аргумента")
            return args[0] * args[1]
        elif op == 'ord':
            if len(args) != 1:
                raise SyntaxError(f"Функция ord требует 1 аргумент")
            if not isinstance(args[0], str) or len(args[0]) != 1:
                raise SyntaxError(f"Функция ord применяется к одиночному символу")
            return ord(args[0])
        else:
            raise SyntaxError(f"Неизвестная операция: {op}")

    def parse_name(self) -> str:
        """Парсинг имен переменных"""
        pattern = r'[a-zA-Z][_a-zA-Z0-9]*'
        match = re.match(pattern, self.text[self.pos:])

        if not match:
            raise SyntaxError(f"Ошибка в имени на позиции {self.pos}")

        name = match.group(0)
        self.pos += len(name)
        return name

    def peek(self) -> str:
        """Посмотреть текущий символ"""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return ''

    def skip_whitespace(self):
        """Пропустить пробелы и переносы строк"""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1


def main():
    """Основная функция"""
    try:
        # Чтение из стандартного ввода
        input_text = sys.stdin.read()

        # Парсинг конфигурации
        parser = ConfigParser()
        config = parser.parse(input_text)

        # Вывод в формате JSON
        json.dump(config, sys.stdout, indent=2, ensure_ascii=False)

    except SyntaxError as e:
        print(f"Ошибка синтаксиса: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()