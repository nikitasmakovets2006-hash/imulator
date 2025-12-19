# DZ.py
import sys
import json
import re
from typing import List, Union, Dict, Any

class TokenType:
    """Типы токенов"""
    EOF = "EOF"
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    LBRACKET = "LBRACKET"      # [
    RBRACKET = "RBRACKET"      # ]
    SEMICOLON = "SEMICOLON"    # ;
    VAR = "VAR"                # var
    AT = "AT"                  # @
    LPAREN = "LPAREN"          # (
    RPAREN = "RPAREN"          # )
    PLUS = "PLUS"              # +
    MINUS = "MINUS"            # -
    MULTIPLY = "MULTIPLY"      # *
    ORD = "ORD"                # ord


class Token:
    """Токен с типом и значением"""
    def __init__(self, type_: str, value: Any = None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """Лексический анализатор"""

    # Регулярное выражение для чисел (включая научную нотацию)
    NUMBER_REGEX = re.compile(r'-?(\d+|\d+\.\d*|\.\d+)([eE][-+]?\d+)?')

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.len = len(text)
        self.line = 1
        self.col = 1

    def error(self, msg: str):
        """Генерация сообщения об ошибке"""
        raise SyntaxError(f"Строка {self.line}, колонка {self.col}: {msg}")

    def peek(self) -> str:
        """Посмотреть следующий символ"""
        return self.text[self.pos] if self.pos < self.len else ''

    def advance(self):
        """Перейти к следующему символу"""
        if self.peek() == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1

    def skip_whitespace(self):
        """Пропуск пробельных символов"""
        while self.pos < self.len and self.peek() in ' \t\r\n':
            self.advance()

    def read_string(self) -> str:
        """Чтение строки в кавычках"""
        self.advance()  # пропускаем открывающую кавычку
        start = self.pos
        while self.pos < self.len:
            ch = self.peek()
            if ch == '"':
                value = self.text[start:self.pos]
                self.advance()  # пропускаем закрывающую кавычку
                return value
            elif ch == '\\':  # обработка escape-последовательностей
                self.advance()
            self.advance()
        self.error("Незакрытая строка")

    def read_number(self) -> Union[int, float]:
        """Чтение числа"""
        start = self.pos
        while self.pos < self.len:
            ch = self.peek()
            if not (ch.isdigit() or ch in '.eE+-'):
                break
            self.advance()

        num_str = self.text[start:self.pos]
        try:
            # Проверяем, содержит ли число точку или научную нотацию
            if '.' in num_str or 'e' in num_str.lower():
                return float(num_str)
            return int(num_str)
        except ValueError:
            self.error(f"Некорректное число: {num_str}")

    def read_identifier(self) -> str:
        """Чтение идентификатора"""
        start = self.pos
        while self.pos < self.len:
            ch = self.peek()
            if not (ch.isalnum() or ch == '_'):
                break
            self.advance()
        return self.text[start:self.pos]

    def next_token(self) -> Token:
        """Получение следующего токена"""
        self.skip_whitespace()

        if self.pos >= self.len:
            return Token(TokenType.EOF)

        ch = self.peek()

        # Строка
        if ch == '"':
            value = self.read_string()
            return Token(TokenType.STRING, value)

        # Число
        if ch.isdigit() or (ch == '-' and self.pos + 1 < self.len and self.text[self.pos + 1].isdigit()):
            # Проверяем по регулярному выражению
            match = self.NUMBER_REGEX.match(self.text[self.pos:])
            if match:
                num_str = match.group(0)
                self.pos += len(num_str)
                # Обновляем позицию строки и колонки
                lines = num_str.count('\n')
                if lines > 0:
                    self.line += lines
                    self.col = len(num_str.split('\n')[-1]) + 1
                else:
                    self.col += len(num_str)

                try:
                    if '.' in num_str or 'e' in num_str.lower():
                        value = float(num_str)
                    else:
                        value = int(num_str)
                except ValueError:
                    self.error(f"Некорректное число: {num_str}")
                return Token(TokenType.NUMBER, value)

        # Идентификаторы и ключевые слова
        if ch.isalpha() or ch == '_':
            ident = self.read_identifier()
            if ident == 'var':
                return Token(TokenType.VAR, ident)
            elif ident == 'ord':
                return Token(TokenType.ORD, ident)
            else:
                return Token(TokenType.IDENTIFIER, ident)

        # Символы
        if ch == '@':
            self.advance()
            return Token(TokenType.AT, ch)
        elif ch == '[':
            self.advance()
            return Token(TokenType.LBRACKET, ch)
        elif ch == ']':
            self.advance()
            return Token(TokenType.RBRACKET, ch)
        elif ch == ';':
            self.advance()
            return Token(TokenType.SEMICOLON, ch)
        elif ch == '(':
            self.advance()
            return Token(TokenType.LPAREN, ch)
        elif ch == ')':
            self.advance()
            return Token(TokenType.RPAREN, ch)
        elif ch == '+':
            self.advance()
            return Token(TokenType.PLUS, ch)
        elif ch == '-':
            self.advance()
            return Token(TokenType.MINUS, ch)
        elif ch == '*':
            self.advance()
            return Token(TokenType.MULTIPLY, ch)

        self.error(f"Неизвестный символ: {ch!r}")


class Parser:
    """Синтаксический анализатор"""

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.next_token()
        self.constants: Dict[str, Any] = {}

    def error(self, msg: str):
        """Генерация сообщения об ошибке"""
        raise SyntaxError(f"Строка {self.lexer.line}, колонка {self.lexer.col}: {msg}")

    def eat(self, token_type: str):
        """Проверка и потребление токена"""
        if self.current_token.type != token_type:
            self.error(f"Ожидался {token_type}, получен {self.current_token.type}")
        token = self.current_token
        self.current_token = self.lexer.next_token()
        return token

    def parse(self) -> Dict[str, Any]:
        """Парсинг всего файла"""
        config = {}

        while self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.VAR:
                self.parse_constant_declaration()
            else:
                name = self.parse_identifier()
                self.eat(TokenType.SEMICOLON)  # В данном синтаксисе после имени идет ;
                value = self.parse_value()
                config[name] = value

        return config

    def parse_constant_declaration(self):
        """Парсинг объявления константы"""
        self.eat(TokenType.VAR)
        name = self.parse_identifier()
        value = self.parse_value()
        self.constants[name] = value

    def parse_identifier(self) -> str:
        """Парсинг идентификатора"""
        token = self.eat(TokenType.IDENTIFIER)
        return token.value

    def parse_value(self) -> Any:
        """Парсинг значения"""
        token = self.current_token

        if token.type == TokenType.NUMBER:
            return self.parse_number()
        elif token.type == TokenType.STRING:
            return self.parse_string()
        elif token.type == TokenType.LBRACKET:
            return self.parse_array()
        elif token.type == TokenType.AT:
            return self.parse_constant_expression()
        else:
            self.error(f"Ожидалось значение, получен {token.type}")

    def parse_number(self) -> Union[int, float]:
        """Парсинг числа"""
        token = self.eat(TokenType.NUMBER)
        return token.value

    def parse_string(self) -> str:
        """Парсинг строки"""
        token = self.eat(TokenType.STRING)
        return token.value

    def parse_array(self) -> List[Any]:
        """Парсинг массива"""
        self.eat(TokenType.LBRACKET)
        array = []

        if self.current_token.type != TokenType.RBRACKET:
            array.append(self.parse_value())

            while self.current_token.type == TokenType.SEMICOLON:
                self.eat(TokenType.SEMICOLON)
                array.append(self.parse_value())

        self.eat(TokenType.RBRACKET)
        return array

    def parse_constant_expression(self) -> Any:
        """Парсинг константного выражения в префиксной форме"""
        self.eat(TokenType.AT)
        self.eat(TokenType.LPAREN)

        result = self.parse_prefix_expression()

        self.eat(TokenType.RPAREN)
        return result

    def parse_prefix_expression(self) -> Any:
        """Парсинг префиксного выражения"""
        token = self.current_token

        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            left = self.parse_prefix_expression()
            right = self.parse_prefix_expression()
            return left + right

        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            left = self.parse_prefix_expression()
            right = self.parse_prefix_expression()
            return left - right

        elif token.type == TokenType.MULTIPLY:
            self.eat(TokenType.MULTIPLY)
            left = self.parse_prefix_expression()
            right = self.parse_prefix_expression()
            return left * right

        elif token.type == TokenType.ORD:
            self.eat(TokenType.ORD)
            self.eat(TokenType.LPAREN)
            arg = self.parse_prefix_expression()
            self.eat(TokenType.RPAREN)
            # ord() принимает строку и возвращает код первого символа
            if isinstance(arg, str) and len(arg) > 0:
                return ord(arg[0])
            else:
                self.error("Функция ord() ожидает непустую строку")

        elif token.type == TokenType.IDENTIFIER:
            name = self.parse_identifier()
            if name in self.constants:
                return self.constants[name]
            else:
                self.error(f"Неизвестная константа: {name}")

        elif token.type == TokenType.NUMBER:
            return self.parse_number()

        elif token.type == TokenType.STRING:
            return self.parse_string()

        else:
            self.error(f"Неожиданный токен в выражении: {token.type}")


def convert_to_json(input_text: str) -> str:
    """Конвертация входного текста в JSON"""
    try:
        lexer = Lexer(input_text)
        parser = Parser(lexer)
        result = parser.parse()
        return json.dumps(result, indent=2, ensure_ascii=False)
    except SyntaxError as e:
        return f"Ошибка синтаксиса: {e}"
    except Exception as e:
        return f"Ошибка: {e}"


def main():
    """Основная функция для работы с командной строкой"""
    if len(sys.argv) > 1:
        # Чтение из файла, если указан аргумент
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                input_text = f.read()
        except FileNotFoundError:
            print(f"Файл {sys.argv[1]} не найден", file=sys.stderr)
            sys.exit(1)
    else:
        # Чтение из стандартного ввода
        print("Введите конфигурацию (Ctrl+D для завершения):", file=sys.stderr)
        input_text = sys.stdin.read()

    json_output = convert_to_json(input_text)
    print(json_output)


if __name__ == "__main__":
    main()