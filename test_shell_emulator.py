# test_shell_emulator.py

import unittest
from shell_emulator import VirtualFileSystem, ShellEmulator
import os
import zipfile
import sys
from io import StringIO
from datetime import datetime

class TestVirtualFileSystem(unittest.TestCase):
    def setUp(self):
        self.zip_path = 'test_fs.zip'
        # Создаем тестовый zip-файл
        with zipfile.ZipFile(self.zip_path, 'w') as zf:
            zf.writestr('file1.txt', 'Content of file1\nLine2\nLine3')
            zf.writestr('dir1/file2.txt', 'Content of file2')
            zf.writestr('dir1/subdir/file3.txt', 'Content of file3')

        self.vfs = VirtualFileSystem(self.zip_path)

    def tearDown(self):
        # Закрываем виртуальную файловую систему
        self.vfs.close()
        # Удаляем созданный zip-файл
        os.remove(self.zip_path)

    def test_list_dir_root(self):
        dirs, files = self.vfs.list_dir('/')
        self.assertIn('dir1', dirs)
        self.assertIn('file1.txt', files)

    def test_list_dir_subdir(self):
        dirs, files = self.vfs.list_dir('/dir1')
        self.assertIn('subdir', dirs)
        self.assertIn('file2.txt', files)

    def test_change_dir(self):
        self.vfs.change_dir('dir1')
        self.assertEqual(self.vfs.current_dir, '/dir1')
        dirs, files = self.vfs.list_dir('.')
        self.assertIn('subdir', dirs)
        self.assertIn('file2.txt', files)

    def test_change_dir_nonexistent(self):
        with self.assertRaises(FileNotFoundError):
            self.vfs.change_dir('nonexistent')

class TestShellEmulatorCommands(unittest.TestCase):
    def setUp(self):
        self.config_path = 'test_config.ini'
        with open(self.config_path, 'w') as f:
            f.write('[DEFAULT]\n')
            f.write('username = testuser\n')
            f.write('filesystem = test_fs.zip\n')
            f.write('logfile = session_log.xml\n')
        # Создаем тестовый zip-файл
        with zipfile.ZipFile('test_fs.zip', 'w') as zf:
            zf.writestr('file.txt', '\n'.join([f"Line {i}" for i in range(1, 21)]))
            zf.writestr('dir/subfile.txt', 'Subfile content')

        self.emulator = ShellEmulator(self.config_path)

    def tearDown(self):
        # Закрываем эмулятор и виртуальную файловую систему
        self.emulator.close()
        # Удаляем созданные файлы
        os.remove(self.config_path)
        os.remove('test_fs.zip')
        if os.path.exists('session_log.xml'):
            os.remove('session_log.xml')

    def test_tail_command(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('tail file.txt')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('Line 11', output)
        self.assertIn('Line 20', output)
        self.assertNotIn('Line 10', output)

    def test_tail_nonexistent_file(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('tail nonexistent.txt')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('Ошибка', output)

    def test_date_command(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('date')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertTrue(len(output.strip()) > 0)

    def test_date_command_format(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('date')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn(str(datetime.now().year), output)

    def test_mv_command(self):
        self.emulator.execute_command('mv file.txt file_renamed.txt')
        dirs, files = self.emulator.vfs.list_dir('/')
        self.assertIn('file_renamed.txt', files)
        self.assertNotIn('file.txt', files)

    def test_mv_nonexistent_file(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('mv nonexistent.txt file.txt')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('Ошибка', output)

    def test_ls_command(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('ls')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('file.txt', output)

    def test_ls_subdirectory(self):
        self.emulator.execute_command('cd dir')
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('ls')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('subfile.txt', output)

    def test_cd_command(self):
        self.emulator.execute_command('cd /')
        self.assertEqual(self.emulator.vfs.current_dir, '/')
        self.emulator.execute_command('cd dir')
        self.assertEqual(self.emulator.vfs.current_dir, '/dir')

    def test_cd_nonexistent_directory(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('cd nonexistent')
        finally:
            sys.stdout = original_stdout
        output = captured_output.getvalue()
        self.assertIn('Ошибка', output)

    def test_exit_command(self):
        with self.assertRaises(SystemExit):
            self.emulator.execute_command('exit')

    def test_exit_saves_log(self):
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            self.emulator.execute_command('ls')
            try:
                self.emulator.execute_command('exit')
            except SystemExit:
                pass
        finally:
            sys.stdout = original_stdout
        self.assertTrue(os.path.exists('session_log.xml'))


if __name__ == '__main__':
    unittest.main()
