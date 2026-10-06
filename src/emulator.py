"""Вариант 24, этап 2: конфигурация и стартовый скрипт."""

import argparse
import os
import shlex
import tkinter as tk
from tkinter import scrolledtext


VFS_NAME = "vfs"


class CommandError(Exception):
    """Ошибка выполнения команды."""


class Config:
    """Параметры запуска эмулятора."""

    def __init__(self, vfs_path, script_path):
        self.vfs_path = vfs_path
        self.script_path = script_path


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

    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.root.title(f"Эмулятор VFS [{VFS_NAME}]")
        self.output = scrolledtext.ScrolledText(
            root, state="disabled", width=80, height=24
        )
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()
        self.write(f"vfs_path={config.vfs_path}\n")
        self.write(f"script_path={config.script_path}\n")
        self.run_script(config.script_path)

    def write(self, text):
        """Добавляет текст в окно вывода."""
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.configure(state="disabled")
        self.output.see("end")

    def run_line(self, line):
        """Выполняет строку. Возвращает ok, error или exit."""
        self.write(prompt() + line + "\n")
        try:
            result = execute(line)
        except SystemExit:
            return "exit"
        except CommandError as exc:
            self.write(f"error: {exc}\n")
            return "error"
        if result:
            self.write(result + "\n")
        return "ok"

    def run_script(self, path):
        """Выполняет стартовый скрипт, стоп при первой ошибке."""
        if not path or path == "<none>":
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except OSError as exc:
            self.write(f"error: стартовый скрипт: {exc}\n")
            return
        for number, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            status = self.run_line(line)
            if status == "exit":
                self.root.destroy()
                return
            if status == "error":
                self.write(f"стоп: ошибка в строке {number}\n")
                break

    def on_enter(self, _event):
        """Обрабатывает ввод команды."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        if self.run_line(line) == "exit":
            self.root.destroy()


def main():
    """Запускает графический эмулятор."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки")
    parser.add_argument("--vfs", required=True, help="путь к VFS")
    parser.add_argument("--script", default="", help="стартовый скрипт")
    args = parser.parse_args()
    script = args.script or "<none>"
    config = Config(vfs_path=args.vfs, script_path=script)
    root = tk.Tk()
    EmulatorApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
