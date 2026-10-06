"""Вариант 24, этап 1: графический прототип REPL."""

import os
import shlex
import tkinter as tk
from tkinter import scrolledtext


VFS_NAME = "vfs"


class CommandError(Exception):
    """Ошибка выполнения команды."""


def parse(line):
    """Разбирает ввод: команда и аргументы с раскрытием переменных."""
    try:
        parts = shlex.split(line)
    except ValueError as exc:
        raise CommandError("ошибка разбора команды") from exc
    if not parts:
        return None, []
    command = parts[0]
    args = [os.path.expandvars(item) for item in parts[1:]]
    return command, args


def execute(line):
    """Выполняет команду, возвращает текст вывода."""
    command, args = parse(line)
    if command is None:
        return ""
    if command == "exit":
        if args:
            raise CommandError("использование: exit")
        raise SystemExit
    if command == "ls":
        return "ls " + " ".join(args) if args else "ls"
    if command == "cd":
        return "cd " + " ".join(args) if args else "cd"
    raise CommandError(f"неизвестная команда: {command}")


def prompt():
    """Приглашение с именем VFS."""
    return f"{VFS_NAME}:$ "


class EmulatorApp:
    """Графическое окно эмулятора."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"Эмулятор VFS [{VFS_NAME}]")
        self.output = scrolledtext.ScrolledText(
            root, state="disabled", width=80, height=24
        )
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

    def write(self, text):
        """Добавляет текст в окно вывода."""
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.configure(state="disabled")
        self.output.see("end")

    def on_enter(self, _event):
        """Обрабатывает ввод команды."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.write(prompt() + line + "\n")
        try:
            result = execute(line)
        except SystemExit:
            self.root.destroy()
            return
        except CommandError as exc:
            self.write(f"error: {exc}\n")
            return
        if result:
            self.write(result + "\n")


def main():
    """Запускает графический эмулятор."""
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
