import tkinter as tk
from tkinter import scrolledtext, Entry, Frame, Label
import sys

class VFSEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title("VFS - Virtual File System")
        self.current_directory = "/home/user"

        self.create_interface()

        self.output_area.insert(tk.END, f"Добро пожаловать в VFS эмулятор!\n")
        self.output_area.insert(tk.END, f"Текущая директория: {self.current_directory}\n")
        self.output_area.insert(tk.END, "Введите 'help' для списка команд\n")
        self.output_area.insert(tk.END, "-" * 50 + "\n")

        self.input_field.focus()

        self.input_field.bind('<Return>', self.execute_command)

    def create_interface(self):
        main_frame = Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output_area = scrolledtext.ScrolledText(
            main_frame,
            height=20,
            width=80,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_area.pack(fill=tk.BOTH, expand=True)
        self.output_area.config(state=tk.DISABLED)

        input_frame = Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.prompt_label = Label(input_frame, text=f"vfs:{self.current_directory}$ ",
                                  bg='black', fg='green', font=('Courier', 10))
        self.prompt_label.pack(side=tk.LEFT)

        self.input_field = Entry(input_frame, bg='black', fg='white',
                                 insertbackground='white', font=('Courier', 10))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def print_output(self, text):
        self.output_area.config(state=tk.NORMAL)
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.see(tk.END)
        self.output_area.config(state=tk.DISABLED)

    def parse_command(self, command_string):
        parts = command_string.strip().split()
        if not parts:
            return "", []
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        return command, args

    def execute_command(self, event=None):
        command_string = self.input_field.get().strip()

        if not command_string:
            self.update_prompt()
            self.input_field.delete(0, tk.END)
            return

        self.input_field.delete(0, tk.END)

        self.print_output(f"vfs:{self.current_directory}$ {command_string}")

        command, args = self.parse_command(command_string)

        if command == "exit":
            self.exit_shell()
        elif command == "ls":
            self.ls_command(args)
        elif command == "cd":
            self.cd_command(args)
        elif command == "help":
            self.help_command(args)
        elif command == "":
            pass  # Пустая команда
        else:
            self.print_output(f"vfs: команда не найдена: {command}")

        self.update_prompt()

    def update_prompt(self):
        """Обновление приглашения командной строки"""
        self.prompt_label.config(text=f"vfs:{self.current_directory}$ ")

    def ls_command(self, args):
        """Команда ls - заглушка"""
        self.print_output(f"Команда 'ls' выполнена с аргументами: {args}")
        self.print_output("file1.txt  file2.txt  directory1/  directory2/")
        self.print_output("Всего: 4 элемента")

    def cd_command(self, args):
        """Команда cd - заглушка"""
        if len(args) == 0:
            self.current_directory = "/home/user"
            self.print_output(f"Переход в домашнюю директорию: {self.current_directory}")
        elif len(args) == 1:
            if args[0] == "..":
                if self.current_directory != "/":
                    parts = self.current_directory.split('/')
                    self.current_directory = '/'.join(parts[:-1]) or '/'
                self.print_output(f"Текущая директория: {self.current_directory}")
            else:
                new_dir = args[0]
                self.print_output(f"Команда 'cd' пытается перейти в: {new_dir}")
                self.print_output(f"Текущая директория: {self.current_directory}")
        else:
            self.print_output("cd: слишком много аргументов")
            self.print_output("Использование: cd [директория]")

    def help_command(self, args):
        """Команда help - показывает доступные команды"""
        help_text = """
Доступные команды:
  ls [аргументы]    - список файлов и директорий (заглушка)
  cd [директория]   - смена директории (заглушка)
  help              - показать эту справку
  exit              - выход из эмулятора

Примеры:
  ls -l
  cd /home
  cd ..
"""
        self.print_output(help_text)

    def exit_shell(self):
        """Выход из эмулятора"""
        self.print_output("Выход из VFS эмулятора...")
        self.root.quit()

def main():
    root = tk.Tk()
    root.geometry("800x600")

    try:
        root.iconbitmap("vfs_icon.ico")
    except:
        pass

    app = VFSEmulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()