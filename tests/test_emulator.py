import os
import tempfile
import unittest

from src.emulator import VFS, VfsEntry, execute, CommandError


XML = """<vfs>
  <dir path="/home" />
  <dir path="/home/user" />
  <file path="/motd" encoding="plain">Hello</file>
  <file path="/home/user/a.txt" encoding="plain">x
x
y</file>
  <file path="/home/user/d.txt" encoding="base64">SGVsbG8=</file>
</vfs>
"""


def make_vfs():
    """Грузит VFS из временного XML."""
    temp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    )
    temp.write(XML)
    temp.close()
    vfs = VFS.from_xml(temp.name)
    os.unlink(temp.name)
    return vfs


class EmulatorTest(unittest.TestCase):
    def setUp(self):
        self.vfs = make_vfs()
        self.session = {"cwd": "/", "history": []}

    def do(self, line):
        """Команда в тестовой сессии."""
        return execute(line, self.session, self.vfs)

    def test_ls_root(self):
        self.assertEqual(self.do("ls /"), "home  motd")

    def test_cd_and_ls(self):
        self.do("cd /home/user")
        self.assertEqual(self.session["cwd"], "/home/user")
        self.assertEqual(self.do("ls"), "a.txt  d.txt")

    def test_bad_cd(self):
        with self.assertRaises(CommandError):
            self.do("cd /missing")

    def test_cat(self):
        self.assertEqual(self.do("cat /motd"), "Hello")

    def test_cat_base64(self):
        self.assertEqual(
            self.do("cat /home/user/d.txt"), "Hello")

    def test_cat_missing(self):
        with self.assertRaises(CommandError):
            self.do("cat /missing")

    def test_uniq(self):
        self.assertEqual(
            self.do("uniq /home/user/a.txt"), "x\ny")

    def test_uniq_count(self):
        self.assertEqual(
            self.do("uniq -c /home/user/a.txt"), "2 x\n1 y")

    def test_mv(self):
        self.do("mv /home/user/a.txt /home/user/b.txt")
        self.assertIn("/home/user/b.txt", self.vfs.entries)
        self.assertNotIn("/home/user/a.txt", self.vfs.entries)

    def test_mv_missing(self):
        with self.assertRaises(CommandError):
            self.do("mv /missing /x")

    def test_chown(self):
        self.do("chown student /motd")
        self.assertEqual(self.vfs.entries["/motd"].owner,
                         "student")

    def test_chown_missing(self):
        with self.assertRaises(CommandError):
            self.do("chown x /missing")

    def test_unknown(self):
        with self.assertRaises(CommandError):
            self.do("bogus")

    def test_bad_vfs(self):
        temp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False)
        temp.write("<vfs><oops></vfs>")
        temp.close()
        with self.assertRaises(RuntimeError):
            VFS.from_xml(temp.name)
        os.unlink(temp.name)


if __name__ == "__main__":
    unittest.main()
