import tkinter as tk
from tkinter import scrolledtext

class VFSEmulator:
    def __init__(self):
        self.commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit
        }

    def cmd_ls(self, args):
        """Команда ls - вывод списка файлов"""
        return f"ls called with args: {args}"

    def cmd_cd(self, args):
        """Команда cd - смена директории"""
        if len(args) != 1:
            return "cd: invalid arguments - usage: cd <directory>"
        return f"cd called with args: {args}"

    def cmd_exit(self, args):
        """Команда exit - выход из эмулятора"""
        return "exit"

    def parse_command(self, input_line):
        """Парсинг введенной команды и аргументов"""
        parts = input_line.strip().split()
        if not parts:
            return ""

        cmd = parts[0]
        args = parts[1:]

        if cmd in self.commands:
            return self.commands[cmd](args)
        else:
            return f"Error: unknown command '{cmd}'"

class VFSGUI:
    def __init__(self, root):
        self.root = root
        self.vfs = VFSEmulator()

        # Настройка главного окна
        self.root.title("VFS Emulator")
        self.root.geometry("800x600")

        # Создание текстовой области для вывода
        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            width=80,
            height=30,
            bg='black',
            fg='white',
            insertbackground='white',
            font=('Consolas', 10)
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Создание поля ввода
        self.entry = tk.Entry(
            root,
            bg='black',
            fg='white',
            insertbackground='white',
            font=('Consolas', 10)
        )
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind('<Return>', self.execute_command)
        self.entry.focus()

        # Блокировка редактирования текстовой области
        self.text_area.config(state=tk.DISABLED)

        # Отображение приветственного сообщения
        self.display_welcome()

    def display_welcome(self):
        """Отображение приветственного сообщения"""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, "=" * 60 + "\n")
        self.text_area.insert(tk.END, "Welcome to VFS Emulator - Virtual File System\n")
        self.text_area.insert(tk.END, "=" * 60 + "\n")
        self.text_area.insert(tk.END, "Available commands: ls, cd, exit\n")
        self.text_area.insert(tk.END, "Type 'exit' to quit the emulator\n")
        self.text_area.insert(tk.END, "-" * 60 + "\n\n")
        self.text_area.insert(tk.END, "$ ")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

    def execute_command(self, event):
        """Выполнение команды из поля ввода"""
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        # Пропуск пустых команд
        if not command:
            return

        # Вывод команды в текстовую область
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{command}\n")

        # Парсинг и выполнение команды
        result = self.vfs.parse_command(command)
        if result:
            self.text_area.insert(tk.END, f"{result}\n")

        # Обработка команды exit
        if result == "exit":
            self.text_area.insert(tk.END, "Goodbye!\n")
            self.text_area.config(state=tk.DISABLED)
            self.root.after(1000, self.root.quit)  # Задержка перед выходом
            return

        # Добавление приглашения для следующей команды
        self.text_area.insert(tk.END, "$ ")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

def main():
    """Основная функция запуска эмулятора"""
    root = tk.Tk()
    app = VFSGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()