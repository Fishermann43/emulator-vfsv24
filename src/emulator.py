"""Вариант 24, этап 3: VFS из XML."""

import argparse
import base64
import os
import shlex
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import scrolledtext


VFS_NAME = "vfs"


class CommandError(Exception):
    """Ошибка выполнения команды."""


class VfsEntry:
    """Элемент виртуальной файловой системы."""

    def __init__(self, path, kind, content="", encoding="plain",
                 owner="root"):
        self.path = path
        self.kind = kind
        self.content = content
        self.encoding = encoding
        self.owner = owner


class VFS:
    """Виртуальная файловая система."""

    def __init__(self):
        self.entries = {}

    @classmethod
    def from_xml(cls, path):
        """Загружает VFS из XML-файла."""
        result = cls()
        try:
            tree = ET.parse(path)
        except FileNotFoundError:
            raise RuntimeError(f"файл VFS не найден: {path}")
        except ET.ParseError as exc:
            raise RuntimeError(f"неверный формат VFS: {exc}")
        except OSError as exc:
            raise RuntimeError(f"чтение VFS: {exc}")
        root = tree.getroot()
        if root.tag != "vfs":
            raise RuntimeError("формат VFS: нужен <vfs>")
        for node in root:
            result._add_node(node)
        result._add_parent_dirs()
        if "/" not in result.entries:
            result.entries["/"] = VfsEntry("/", "dir")
        return result

    def _add_node(self, node):
        """Добавляет один элемент из XML-узла."""
        owner = node.get("owner") or "root"
        if node.tag == "dir":
            path = self.normalize(node.get("path") or "/")
            self.entries[path] = VfsEntry(path, "dir", owner=owner)
        elif node.tag == "file":
            path = self.normalize(node.get("path") or "/")
            encoding = (node.get("encoding") or "plain").lower()
            content = node.text or ""
            if encoding == "base64":
                try:
                    content = base64.b64decode(
                        content.encode()).decode("utf-8")
                except (ValueError, UnicodeError) as exc:
                    raise RuntimeError(
                        f"ошибка base64 для {path}") from exc
            self.entries[path] = VfsEntry(
                path, "file", content, encoding, owner)
        else:
            raise RuntimeError(f"элемент: {node.tag}")

    def _add_parent_dirs(self):
        """Добавляет недостающие каталоги."""
        for path in list(self.entries):
            parent = self.parent(path)
            while parent and parent not in self.entries:
                self.entries[parent] = VfsEntry(parent, "dir")
                parent = self.parent(parent)

    @staticmethod
    def normalize(path):
        """Приводит путь к абсолютному виду."""
        if not path:
            return "/"
        parts = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/" + "/".join(parts)

    @staticmethod
    def parent(path):
        """Возвращает родительский каталог."""
        path = VFS.normalize(path)
        if path == "/":
            return ""
        value = path.rsplit("/", 1)[0]
        return value or "/"

    def resolve(self, path, cwd):
        """Делает путь абсолютным виртуальным."""
        if path.startswith("/"):
            return self.normalize(path)
        return self.normalize(cwd + "/" + path)

    def list_dir(self, path):
        """Имена элементов каталога."""
        path = self.normalize(path)
        entry = self.entries.get(path)
        if entry is None or entry.kind != "dir":
            raise CommandError(f"нет такого каталога: {path}")
        prefix = "/" if path == "/" else path + "/"
        names = []
        for item_path in self.entries:
            if not item_path.startswith(prefix):
                continue
            if item_path == path:
                continue
            rest = item_path[len(prefix):]
            if "/" not in rest:
                names.append(rest)
        return sorted(set(names))


class Config:
    """Параметры запуска эмулятора."""

    def __init__(self, vfs_path, script_path):
        self.vfs_path = vfs_path
        self.script_path = script_path


def parse(line):
    """Разбирает ввод, раскрывая переменные."""
    try:
        parts = shlex.split(line)
    except ValueError as exc:
        raise CommandError("ошибка разбора") from exc
    if not parts:
        return None, []
    command = parts[0]
    args = [os.path.expandvars(item) for item in parts[1:]]
    return command, args


def execute(line, session, vfs):
    """Выполняет команду, возвращает вывод."""
    command, args = parse(line)
    if command is None:
        return ""
    if command == "exit":
        if args:
            raise CommandError("использование: exit")
        raise SystemExit
    if command == "ls":
        return cmd_ls(args, session, vfs)
    if command == "cd":
        return cmd_cd(args, session, vfs)
    if command == "cat":
        return cmd_cat(args, session, vfs)
    if command == "uniq":
        return cmd_uniq(args, session, vfs)
    if command == "mv":
        return cmd_mv(args, session, vfs)
    if command == "chown":
        return cmd_chown(args, session, vfs)
    raise CommandError(f"неизвестная команда: {command}")


def cmd_ls(args, session, vfs):
    """Содержимое виртуального каталога."""
    if len(args) > 1:
        raise CommandError("использование: ls [путь]")
    if args:
        path = vfs.resolve(args[0], session["cwd"])
    else:
        path = session["cwd"]
    return "  ".join(vfs.list_dir(path))


def cmd_cd(args, session, vfs):
    """Меняет виртуальный текущий каталог."""
    if len(args) > 1:
        raise CommandError("использование: cd [каталог]")
    if args:
        path = vfs.resolve(args[0], session["cwd"])
    else:
        path = "/"
    entry = vfs.entries.get(path)
    if entry is None or entry.kind != "dir":
        raise CommandError(f"нет такого каталога: {path}")
    session["cwd"] = path
    return ""


def cmd_cat(args, session, vfs):
    """Выводит содержимое файла VFS."""
    if len(args) != 1:
        raise CommandError("использование: cat файл")
    path = vfs.resolve(args[0], session["cwd"])
    entry = vfs.entries.get(path)
    if entry is None or entry.kind != "file":
        raise CommandError(f"нет такого файла: {path}")
    return entry.content


def cmd_uniq(args, session, vfs):
    """Убирает соседние повторы строк файла."""
    count_mode = False
    rest = list(args)
    if rest and rest[0] == "-c":
        count_mode = True
        rest = rest[1:]
    if len(rest) != 1:
        raise CommandError("использование: uniq [-c] файл")
    path = vfs.resolve(rest[0], session["cwd"])
    entry = vfs.entries.get(path)
    if entry is None or entry.kind != "file":
        raise CommandError(f"нет такого файла: {path}")
    out = []
    prev = None
    count = 0
    for row in entry.content.splitlines():
        if row == prev:
            count += 1
            continue
        if prev is not None:
            out.append(_uniq_row(prev, count, count_mode))
        prev = row
        count = 1
    if prev is not None:
        out.append(_uniq_row(prev, count, count_mode))
    return "\n".join(out)


def _uniq_row(text, count, count_mode):
    """Форматирует строку вывода uniq."""
    if count_mode:
        return f"{count} {text}"
    return text


def cmd_mv(args, session, vfs):
    """Перемещает файл или каталог в памяти."""
    if len(args) != 2:
        raise CommandError("использование: mv src dst")
    src = vfs.resolve(args[0], session["cwd"])
    dst = vfs.resolve(args[1], session["cwd"])
    entry = vfs.entries.get(src)
    if entry is None:
        raise CommandError(f"нет такого файла: {src}")
    if src == "/":
        raise CommandError("нельзя переместить корень")
    target = dst
    dst_entry = vfs.entries.get(dst)
    if dst_entry is not None and dst_entry.kind == "dir":
        base = src.rsplit("/", 1)[1]
        target = dst.rstrip("/") + "/" + base
        target = vfs.normalize(target)
    if target == src or target.startswith(src + "/"):
        raise CommandError("нельзя внутрь себя")
    if target in vfs.entries:
        raise CommandError(f"уже существует: {target}")
    parent = vfs.parent(target)
    parent_entry = vfs.entries.get(parent)
    if parent_entry is None or parent_entry.kind != "dir":
        raise CommandError(f"нет каталога: {parent}")
    moved = {}
    for path, item in vfs.entries.items():
        if path == src or path.startswith(src + "/"):
            moved[path] = item
    for path in moved:
        del vfs.entries[path]
    for path, item in moved.items():
        item.path = target + path[len(src):]
        vfs.entries[item.path] = item
    return ""


def cmd_chown(args, session, vfs):
    """Меняет владельца файла в памяти."""
    if len(args) != 2:
        raise CommandError("использование: chown owner file")
    path = vfs.resolve(args[1], session["cwd"])
    entry = vfs.entries.get(path)
    if entry is None:
        raise CommandError(f"нет такого файла: {path}")
    entry.owner = args[0]
    return ""


def prompt_for(session):
    """Приглашение с именем VFS и каталогом."""
    return f"{VFS_NAME}:{session['cwd']}$ "


def prompt():
    """Приглашение с именем VFS."""
    return f"{VFS_NAME}:$ "


class EmulatorApp:
    """Графическое окно эмулятора."""

    def __init__(self, root, config, vfs, vfs_error):
        self.root = root
        self.config = config
        self.vfs = vfs
        self.session = {"cwd": "/", "history": []}
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
        if vfs_error:
            self.write(f"error: {vfs_error}\n")
            return
        self.write(f"vfs: элементов: {len(vfs.entries)}\n")
        self.run_script(config.script_path)

    def write(self, text):
        """Добавляет текст в окно вывода."""
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.configure(state="disabled")
        self.output.see("end")

    def run_line(self, line):
        """Выполняет строку: ok, error или exit."""
        self.write(prompt_for(self.session) + line + "\n")
        if line.strip():
            self.session["history"].append(line)
        try:
            result = execute(line, self.session, self.vfs)
        except SystemExit:
            return "exit"
        except CommandError as exc:
            self.write(f"error: {exc}\n")
            return "error"
        if result:
            self.write(result + "\n")
        return "ok"

    def run_script(self, path):
        """Скрипт, стоп при первой ошибке."""
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
    parser = argparse.ArgumentParser(
        description="Эмулятор")
    parser.add_argument("--vfs", required=True, help="путь к VFS")
    parser.add_argument(
        "--script", default="", help="скрипт"
    )
    args = parser.parse_args()
    script = args.script or "<none>"
    config = Config(vfs_path=args.vfs, script_path=script)
    try:
        vfs = VFS.from_xml(config.vfs_path)
        vfs_error = ""
    except RuntimeError as exc:
        vfs = VFS()
        vfs_error = str(exc)
    root = tk.Tk()
    EmulatorApp(root, config, vfs, vfs_error)
    root.mainloop()


if __name__ == "__main__":
    main()
