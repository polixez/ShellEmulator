# shell_emulator.py

import os
import sys
import zipfile
import io
import configparser
import xml.etree.ElementTree as ET
from datetime import datetime

class VirtualFileSystem:
    def __init__(self, zip_path):
        self.zip_file = zipfile.ZipFile(zip_path)
        self.current_dir = '/'
        self.files = self._build_file_tree()
        self.zip_path = zip_path

    def close(self):
        self.zip_file.close()

    def _build_file_tree(self):
        files = {}
        for file_info in self.zip_file.infolist():
            files['/' + file_info.filename.rstrip('/')] = file_info
        return files

    def list_dir(self, path):
        path = self._normalize_path(path)
        if not path.endswith('/'):
            path += '/'
        dirs = set()
        files = set()
        for file_path in self.files.keys():
            if file_path.startswith(path) and file_path != path:
                rel_path = file_path[len(path):]
                if '/' in rel_path:
                    dirs.add(rel_path.split('/')[0])
                else:
                    files.add(rel_path)
        return sorted(dirs), sorted(files)

    def change_dir(self, path):
        new_path = self._normalize_path(path)
        if any(f.startswith(new_path) for f in self.files.keys()) or new_path == '/':
            self.current_dir = new_path
        else:
            raise FileNotFoundError(f"Нет такого каталога: {path}")

    def read_file(self, path):
        file_path = self._normalize_path(path)
        if file_path in self.files and not self.files[file_path].is_dir():
            with self.zip_file.open(self.files[file_path]) as f:
                return f.read().decode('utf-8')
        else:
            raise FileNotFoundError(f"Нет такого файла: {path}")

    def move(self, src, dst):
        src_path = self._normalize_path(src)
        dst_path = self._normalize_path(dst)
        if src_path in self.files:
            self.files[dst_path] = self.files.pop(src_path)
        else:
            raise FileNotFoundError(f"Нет такого файла или каталога: {src}")

    def _normalize_path(self, path):
        if not path.startswith('/'):
            path = os.path.join(self.current_dir, path)
        return os.path.normpath(path).replace('\\', '/')

class ShellEmulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.vfs = VirtualFileSystem(self.fs_archive)
        self.log_entries = []
        self.user = self.username
        self.run_startup_script()

    def load_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.username = config['DEFAULT']['username']
        self.fs_archive = config['DEFAULT']['filesystem']
        self.log_file = config['DEFAULT']['logfile']
        self.startup_script = config['DEFAULT'].get('startup_script')

    def run_startup_script(self):
        if self.startup_script and os.path.exists(self.startup_script):
            with open(self.startup_script, 'r') as script:
                for line in script:
                    self.execute_command(line.strip())

    def log(self, command):
        entry = {
            'user': self.user,
            'datetime': datetime.now().isoformat(),
            'command': command
        }
        self.log_entries.append(entry)

    def save_log(self):
        root = ET.Element('session')
        for entry in self.log_entries:
            action = ET.SubElement(root, 'action')
            user = ET.SubElement(action, 'user')
            user.text = entry['user']
            dt = ET.SubElement(action, 'datetime')
            dt.text = entry['datetime']
            cmd = ET.SubElement(action, 'command')
            cmd.text = entry['command']
        tree = ET.ElementTree(root)
        tree.write(self.log_file)

    def execute_command(self, command_line):
        self.log(command_line)
        if not command_line:
            return
        parts = command_line.split()
        cmd = parts[0]
        args = parts[1:]

        try:
            if cmd == 'ls':
                self.ls(args)
            elif cmd == 'cd':
                self.cd(args)
            elif cmd == 'exit':
                self.exit_shell()
            elif cmd == 'mv':
                self.mv(args)
            elif cmd == 'tail':
                self.tail(args)
            elif cmd == 'date':
                self.show_date()
            else:
                print(f"Неизвестная команда: {cmd}")
        except Exception as e:
            print(f"Ошибка: {e}")

    def prompt(self):
        return f"{self.user}@virtual:{self.vfs.current_dir}$ "

    def ls(self, args):
        path = args[0] if args else self.vfs.current_dir
        dirs, files = self.vfs.list_dir(path)
        for d in dirs:
            print(f"{d}/")
        for f in files:
            print(f)

    def cd(self, args):
        if not args:
            print("cd: отсутствует аргумент")
            return
        path = args[0]
        self.vfs.change_dir(path)

    def exit_shell(self):
        self.save_log()
        sys.exit(0)

    def mv(self, args):
        if len(args) != 2:
            print("mv: требуется указать исходный и целевой путь")
            return
        src, dst = args
        self.vfs.move(src, dst)

    def tail(self, args):
        if not args:
            print("tail: отсутствует файл")
            return
        path = args[0]
        content = self.vfs.read_file(path)
        lines = content.strip().split('\n')
        for line in lines[-10:]:
            print(line)

    def show_date(self):
        print(datetime.now().strftime("%a %b %d %H:%M:%S %Y"))

    def run(self):
        while True:
            try:
                command_line = input(self.prompt())
                self.execute_command(command_line)
            except EOFError:
                self.exit_shell()
            except KeyboardInterrupt:
                print()
                self.exit_shell()

    def close(self):
        self.vfs.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python shell_emulator.py <config.ini>")
        sys.exit(1)
    emulator = ShellEmulator(sys.argv[1])
    emulator.run()