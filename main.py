import sys
import os
import tkinter as tk
from tkinter import scrolledtext
import argparse

class VFSEmulator:
    def __init__(self, vfs_path=None, startup_script=None):
        self.vfs_path = vfs_path or os.getcwd()
        self.startup_script = startup_script
        self.commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit
        }

    def cmd_ls(self, args):
        return f"ls called with args: {args}"

    def cmd_cd(self, args):
        if len(args) != 1:
            return "cd: invalid arguments"
        return f"cd called with args: {args}"

    def cmd_exit(self, args):
        return "exit"

    def parse_command(self, input_line):
        parts = input_line.strip().split()
        if not parts:
            return ""

        cmd = parts[0]
        args = parts[1:]

        if cmd in self.commands:
            return self.commands[cmd](args)
        else:
            return f"Error: unknown command '{cmd}'"

    def execute_script(self, script_path):
        if not os.path.exists(script_path):
            return f"Error: script file '{script_path}' not found"

        results = []
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    results.append(f"$ {line}")
                    output = self.parse_command(line)
                    if output:
                        results.append(output)
                        if output == "exit":
                            break
        except Exception as e:
            return f"Error executing script: {str(e)}"

        return "\n".join(results)

class VFSGUI:
    def __init__(self, root, vfs_emulator):
        self.root = root
        self.vfs = vfs_emulator

        self.root.title("VFS Emulator")
        self.root.geometry("800x600")

        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            width=80,
            height=30,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(root, bg='black', fg='white', insertbackground='white')
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind('<Return>', self.execute_command)

        self.text_area.config(state=tk.DISABLED)

        self.display_welcome()

        if self.vfs.startup_script:
            self.execute_startup_script()

    def display_welcome(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, "Welcome to VFS Emulator\n")
        self.text_area.insert(tk.END, f"VFS Path: {self.vfs.vfs_path}\n")
        if self.vfs.startup_script:
            self.text_area.insert(tk.END, f"Startup Script: {self.vfs.startup_script}\n")
        self.text_area.insert(tk.END, "Type 'exit' to quit\n\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

    def execute_startup_script(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"\nExecuting startup script: {self.vfs.startup_script}\n")
        result = self.vfs.execute_script(self.vfs.startup_script)
        self.text_area.insert(tk.END, f"\n{result}\n")
        self.text_area.insert(tk.END, "\nStartup script execution completed.\n\n$ ")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

    def execute_command(self, event):
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if not command:
            return

        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"$ {command}\n")

        result = self.vfs.parse_command(command)
        if result:
            self.text_area.insert(tk.END, f"{result}\n")

        if result == "exit":
            self.root.quit()
            return

        self.text_area.insert(tk.END, "$ ")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

def main():
    parser = argparse.ArgumentParser(description='VFS Emulator')
    parser.add_argument('--vfs-path', help='Path to VFS physical location')
    parser.add_argument('--startup-script', help='Path to startup script')

    args = parser.parse_args()

    print("VFS Emulator starting with parameters:")
    print(f"  VFS Path: {args.vfs_path}")
    print(f"  Startup Script: {args.startup_script}")

    vfs = VFSEmulator(args.vfs_path, args.startup_script)

    root = tk.Tk()
    app = VFSGUI(root, vfs)
    root.mainloop()

if __name__ == "__main__":
    main()