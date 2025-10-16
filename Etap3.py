import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys
import os
import json
import base64
import argparse

class VFS:
    def __init__(self):
        self.root = {"type": "directory", "children": {}}
        self.current_path = "/"

    def load_from_json(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.root = data
            self.current_path = "/"
            return True, "VFS успешно загружена из файла"
        except FileNotFoundError:
            return False, f"Ошибка: Файл {json_path} не найден"
        except json.JSONDecodeError:
            return False, f"Ошибка: Неверный формат JSON файла {json_path}"
        except Exception as e:
            return False, f"Ошибка загрузки VFS: {str(e)}"

    def create_default(self):
        self.root = {
            "type": "directory",
            "children": {
                "home": {
                    "type": "directory",
                    "children": {
                        "user": {
                            "type": "directory",
                            "children": {
                                "documents": {
                                    "type": "directory",
                                    "children": {
                                        "readme.txt": {
                                            "type": "file",
                                            "content": "Добро пожаловать в VFS!"
                                        }
                                    }
                                },
                                "file1.txt": {
                                    "type": "file",
                                    "content": "Содержимое файла 1"
                                }
                            }
                        }
                    }
                },
                "bin": {
                    "type": "directory",
                    "children": {
                        "ls": {"type": "file", "content": "эмулятор команды ls"},
                        "cd": {"type": "file", "content": "эмулятор команды cd"}
                    }
                },
                "etc": {
                    "type": "directory",
                    "children": {
                        "config.json": {"type": "file", "content": "{}"}
                    }
                }
            }
        }
        self.current_path = "/"

    def get_current_directory(self):
        path_parts = [part for part in self.current_path.split('/') if part]
        current_dir = self.root

        for part in path_parts:
            if part in current_dir.get("children", {}):
                current_dir = current_dir["children"][part]
            else:
                return None

        return current_dir

    def resolve_path(self, path):
        if path.startswith('/'):
            path_parts = [part for part in path.split('/') if part]
            current_dir = self.root
        else:
            path_parts = [part for part in path.split('/') if part]
            current_dir = self.get_current_directory()
            if current_dir is None:
                return None, "Текущая директория не существует"

        for part in path_parts:
            if part == '..':
                if self.current_path != '/':
                    path_parts = [p for p in self.current_path.split('/') if p][:-1]
                    self.current_path = '/' + '/'.join(path_parts) if path_parts else '/'
                current_dir = self.get_current_directory()
            elif part == '.':
                continue
            else:
                if part in current_dir.get("children", {}):
                    current_dir = current_dir["children"][part]
                else:
                    return None, f"Путь не найден: {path}"

        return current_dir, None

class ShellEmulator:
    def __init__(self, vfs_path=None, startup_script=None):
        self.vfs = VFS()
        self.startup_script = startup_script

        if vfs_path:
            success, message = self.vfs.load_from_json(vfs_path)
            if not success:
                print(f"Отладочный вывод: {message}")
                self.vfs.create_default()
                print("Отладочный вывод: Использована VFS по умолчанию")
        else:
            self.vfs.create_default()
            print("Отладочный вывод: Создана VFS по умолчанию")

        self.root = tk.Tk()
        self.root.title("VFS Shell Emulator")
        self.setup_gui()

        if self.startup_script:
            self.execute_startup_script(self.startup_script)

    def setup_gui(self):
        self.root.geometry("800x600")

        self.output_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Courier New', 10)
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_area.config(state=tk.DISABLED)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(input_frame, text="$").pack(side=tk.LEFT)
        self.input_entry = tk.Entry(input_frame, bg='black', fg='white', insertbackground='white')
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind('<Return>', self.execute_command)
        self.input_entry.focus()

        self.print_output("Добро пожаловать в VFS Shell Emulator!\n")
        self.print_output("Доступные команды: ls, cd, exit, vfs-init\n")
        self.update_prompt()

    def print_output(self, text):
        self.output_area.config(state=tk.NORMAL)
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.config(state=tk.DISABLED)

    def update_prompt(self):
        self.print_output(f"\n{self.vfs.current_path} $ ")

    def parse_command(self, command_string):
        parts = command_string.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]

    def execute_startup_script(self, script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                self.print_output(f"\n# {line}\n")
                success, output = self.execute_single_command(line)
                if not success:
                    self.print_output(f"Ошибка в строке {line_num}: {output}\n")
                    break

        except FileNotFoundError:
            self.print_output(f"Ошибка: Стартовый скрипт {script_path} не найден\n")
        except Exception as e:
            self.print_output(f"Ошибка выполнения скрипта: {str(e)}\n")

    def execute_single_command(self, command_string):
        command, args = self.parse_command(command_string)

        if command == "ls":
            return self.cmd_ls(args)
        elif command == "cd":
            return self.cmd_cd(args)
        elif command == "exit":
            return self.cmd_exit(args)
        elif command == "vfs-init":
            return self.cmd_vfs_init(args)
        elif command == "":
            return True, ""
        else:
            return False, f"Неизвестная команда: {command}"

    def execute_command(self, event=None):
        command_string = self.input_entry.get()
        self.input_entry.delete(0, tk.END)

        self.print_output(command_string + "\n")

        success, output = self.execute_single_command(command_string)

        if output:
            self.print_output(output + "\n")

        if not success and "exit" not in command_string:
            self.print_output("Ошибка выполнения команды\n")

        self.update_prompt()

    def cmd_ls(self, args):
        target_path = args[0] if args else self.vfs.current_path

        current_dir, error = self.vfs.resolve_path(target_path)
        if error:
            return False, error

        if current_dir.get("type") != "directory":
            return False, f"{target_path}: Не является директорией"

        children = current_dir.get("children", {})
        if not children:
            return True, ""

        items = []
        for name, item in children.items():
            item_type = "d" if item.get("type") == "directory" else "-"
            items.append(f"{item_type} {name}")

        return True, "\n".join(items)

    def cmd_cd(self, args):
        if not args:
            self.vfs.current_path = "/"
            return True, ""

        target_path = args[0]
        old_path = self.vfs.current_path

        target_dir, error = self.vfs.resolve_path(target_path)
        if error:
            return False, error

        if target_dir.get("type") != "directory":
            return False, f"{target_path}: Не является директорией"

        if target_path.startswith('/'):
            self.vfs.current_path = target_path
        else:
            if self.vfs.current_path == '/':
                self.vfs.current_path = '/' + target_path
            else:
                self.vfs.current_path = self.vfs.current_path + '/' + target_path

        path_parts = [part for part in self.vfs.current_path.split('/') if part]
        self.vfs.current_path = '/' + '/'.join(path_parts) if path_parts else '/'

        return True, ""

    def cmd_exit(self, args):
        self.root.quit()
        return True, ""

    def cmd_vfs_init(self, args):
        self.vfs.create_default()
        return True, "VFS инициализирована по умолчанию"

def create_test_scripts():
    with open('test_basic.py', 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
print("=== Базовое тестирование ===")

print("Тест 1: Запуск без параметров")
import subprocess
result = subprocess.run(['python', 'shell_emulator.py'], capture_output=True, text=True)
print("Результат:", "Успех" if "Добро пожаловать" in result.stdout else "Ошибка")

print("\\\\nТест 2: Запуск с VFS")
result = subprocess.run([
    'python', 'shell_emulator.py', 
    '--vfs', 'test_vfs.json'
], capture_output=True, text=True)
print("Результат:", "Успех" if "VFS успешно загружена" in result.stdout else "Ошибка")

print("\\\\nТест 3: Запуск со стартовым скриптом")
result = subprocess.run([
    'python', 'shell_emulator.py',
    '--script', 'startup_script.txt'
], capture_output=True, text=True)
print("Результат:", "Успех" if "Выполнение команды ls" in result.stdout else "Ошибка")
""")

    with open('test_vfs.py', 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
print("=== Тестирование VFS ===")

import subprocess
import json
import os

test_vfs_minimal = {
    "type": "directory",
    "children": {
        "file1.txt": {"type": "file", "content": "минимальный VFS"}
    }
}

test_vfs_multilevel = {
    "type": "directory",
    "children": {
        "level1": {
            "type": "directory", 
            "children": {
                "level2": {
                    "type": "directory",
                    "children": {
                        "level3": {
                            "type": "directory",
                            "children": {
                                "deep_file.txt": {"type": "file", "content": "глубокий файл"}
                            }
                        }
                    }
                }
            }
        },
        "documents": {
            "type": "directory",
            "children": {
                "doc1.txt": {"type": "file", "content": "документ 1"},
                "doc2.txt": {"type": "file", "content": "документ 2"}
            }
        }
    }
}

with open('minimal_vfs.json', 'w') as f:
    json.dump(test_vfs_minimal, f)

with open('multilevel_vfs.json', 'w') as f:
    json.dump(test_vfs_multilevel, f)

print("\\\\nТест 1: Минимальная VFS")
result = subprocess.run([
    'python', 'shell_emulator.py',
    '--vfs', 'minimal_vfs.json'
], capture_output=True, text=True)
print("Результат:", "Успех" if "VFS успешно загружена" in result.stdout else "Ошибка")

print("\\\\nТест 2: Многоуровневая VFS")  
result = subprocess.run([
    'python', 'shell_emulator.py',
    '--vfs', 'multilevel_vfs.json'
], capture_output=True, text=True)
print("Результат:", "Успех" if "VFS успешно загружена" in result.stdout else "Ошибка")

if os.path.exists('minimal_vfs.json'):
    os.remove('minimal_vfs.json')
if os.path.exists('multilevel_vfs.json'):
    os.remove('multilevel_vfs.json')
""")

    with open('startup_script.txt', 'w', encoding='utf-8') as f:
        f.write("""# Стартовый скрипт для тестирования

ls
cd home
ls
cd user
ls

ls несуществующий_путь
cd несуществующая_директория
unknown_command

vfs-init
ls

cd /
ls
""")

    with open('test_vfs.json', 'w', encoding='utf-8') as f:
        json.dump({
            "type": "directory",
            "children": {
                "custom_dir": {
                    "type": "directory",
                    "children": {
                        "test_file.txt": {
                            "type": "file",
                            "content": "Это тестовый файл из загруженной VFS"
                        }
                    }
                },
                "readme.md": {
                    "type": "file",
                    "content": "# Тестовая VFS"
                }
            }
        }, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='VFS Shell Emulator')
    parser.add_argument('--vfs', help='Путь к файлу VFS (JSON)')
    parser.add_argument('--script', help='Путь к стартовому скрипту')

    args = parser.parse_args()

    print("Отладочный вывод: Параметры командной строки:")
    print(f"  VFS путь: {args.vfs}")
    print(f"  Стартовый скрипт: {args.script}")

    if not os.path.exists('test_vfs.json'):
        create_test_scripts()
        print("Отладочный вывод: Созданы тестовые файлы")

    emulator = ShellEmulator(vfs_path=args.vfs, startup_script=args.script)
    emulator.root.mainloop()

if __name__ == "__main__":
    main()