#  Разрабока эмулятор для языка оболочки ОС
 Эмулятор командной оболочки UNIX-подобной операционной системы на Python.
## Общее описание
Данный проект реализует эмуляцию командной оболочки с поддержкой базовых команд и виртуальной файловой системы, основанной на zip-архиве. Эмулятор предназначен для работы в режиме командной строки (CLI) и максимально приближен к сеансу работы с shell в UNIX-подобных ОС.
## Функции и настройки
### Поддерживаемые команды
• ```ls — вывод списка файлов и каталогов.```

• ```cd — смена текущего каталога.```

• ```exit — выход из эмулятора.```

• ```mv — перемещение или переименование файла или каталога.```

• ```tail — вывод последних 10 строк файла.```

• ```date — отображение текущей даты и времени.```

### Реализация классов и их функций

**Класс VirtualFileSystem**

Инициализация виртуальной файловой системы

````
    def __init__(self, zip_path):
        self.zip_file = zipfile.ZipFile(zip_path)
        self.current_dir = '/'
        self.files = self._build_file_tree()
        self.zip_path = zip_path
````
Закрытие ZIP-архива
````
    def close(self):
        self.zip_file.close()
````
Создание дерева файлов и директорий из ZIP
````
    def _build_file_tree(self):
        files = {}
        for file_info in self.zip_file.infolist():
            files['/' + file_info.filename.rstrip('/')] = file_info
        return files
````
Возврат списков директорий и файлов
````
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
````
Изменение директории на указанную
````
    def change_dir(self, path):
        new_path = self._normalize_path(path)
        if any(f.startswith(new_path) for f in self.files.keys()) or new_path == '/':
            self.current_dir = new_path
        else:
            raise FileNotFoundError(f"Нет такого каталога: {path}")
````
Чтение содержимого файла
````
 def read_file(self, path):
        file_path = self._normalize_path(path)
        if file_path in self.files and not self.files[file_path].is_dir():
            with self.zip_file.open(self.files[file_path]) as f:
                return f.read().decode('utf-8')
        else:
            raise FileNotFoundError(f"Нет такого файла: {path}")
````
Перемещение и переименование файла/директории (move)
````
    def move(self, src, dst):
        src_path = self._normalize_path(src)
        dst_path = self._normalize_path(dst)
        if src_path in self.files:
            self.files[dst_path] = self.files.pop(src_path)
        else:
            raise FileNotFoundError(f"Нет такого файла или каталога: {src}")
````
Нормализование пути
````
    def _normalize_path(self, path):
        if not path.startswith('/'):
            path = os.path.join(self.current_dir, path)
        return os.path.normpath(path).replace('\\', '/')
````

**Класс ShellEmulator**

Инициализация оболочки
````
 def __init__(self, config_path):
        self.load_config(config_path)
        self.vfs = VirtualFileSystem(self.fs_archive)
        self.log_entries = []
        self.user = self.username
        self.run_startup_script()
````
Подгрузка настроек из config.ini
````
    def load_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.username = config['DEFAULT']['username']
        self.fs_archive = config['DEFAULT']['filesystem']
        self.log_file = config['DEFAULT']['logfile']
        self.startup_script = config['DEFAULT'].get('startup_script')
````
Выполнение комманд из стартового скрипта
````
    def run_startup_script(self):
        if self.startup_script and os.path.exists(self.startup_script):
            with open(self.startup_script, 'r') as script:
                for line in script:
                    self.execute_command(line.strip())
````
Логирование
````
    def log(self, command):
        entry = {
            'user': self.user,
            'datetime': datetime.now().isoformat(),
            'command': command
        }
        self.log_entries.append(entry)
````
Сохранение лог всех комманд в файл XML
````
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
````
Выполнение комманды по её имени
````
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
````
Генерация строки приглашения
````
    def prompt(self):
        return f"{self.user}@virtual:{self.vfs.current_dir}$ "
````
Вывод директории (ls)
````
  def ls(self, args):
        path = args[0] if args else self.vfs.current_dir
        dirs, files = self.vfs.list_dir(path)
        for d in dirs:
            print(f"{d}/")
        for f in files:
            print(f)
````
Смена директории (cd)
````
    def cd(self, args):
        if not args:
            print("cd: отсутствует аргумент")
            return
        path = args[0]
        self.vfs.change_dir(path)
````
Сохранение лог и завершение работы оболочки(exit)
````
    def exit_shell(self):
        self.save_log()
        sys.exit(0)
````
Перемещение и переименование файла/директории (mv)
````
    def mv(self, args):
        if len(args) != 2:
            print("mv: требуется указать исходный и целевой путь")
            return
        src, dst = args
        self.vfs.move(src, dst)
````
Вывод последних 10 строк файла (tail)
````
   def tail(self, args):
        if not args:
            print("tail: отсутствует файл")
            return
        path = args[0]
        content = self.vfs.read_file(path)
        lines = content.strip().split('\n')
        for line in lines[-10:]:
            print(line)
````
Вывод текущей даты и времени(date)
````
    def show_date(self):
        print(datetime.now().strftime("%a %b %d %H:%M:%S %Y"))
````
Основной цикл работы оболочки: обрабатывает пользовательский ввод.
````
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
````
Закрытие виртуальной файловой системы
````
    def close(self):
        self.vfs.close()
````

**Основная функция (if __name__ == "__main__")**
````
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python shell_emulator.py <config.ini>")
        sys.exit(1)
    emulator = ShellEmulator(sys.argv[1])
    emulator.run()
````

### Конфигурационный файл
Эмулятор использует конфигурационный файл в формате ini, который содержит следующие настройки:

• ```username — имя пользователя для отображения в приглашении.```

• ```filesystem — путь к архиву виртуальной файловой системы (zip-файл).```

• ```logfile — путь к лог-файлу (формат XML).```

• ```startup_script — путь к стартовому скрипту с командами для выполнения при запуске.```

**Пример** ```config.ini```:
````
[DEFAULT]
username = user
filesystem = virtual_fs.zip
logfile = session_log.xml
startup_script = startup.sh
````

### Логирование
Все действия пользователя в ходе сессии записываются в лог-файл в формате XML. Для каждого действия указываются дата, время и имя пользователя.

### Стартовый скрипт
При запуске эмулятора можно указать стартовый скрипт, содержащий список команд для автоматического выполнения.

**Пример** ```startup.sh```:
````
date
````
## Команды для сборки проекта

1. **Установка зависимостей**:  

   Эмулятор использует стандартные библиотеки Python и не требует установки дополнительных пакетов.

2. **Запуск тестов**:
    
    ````
   python test_shell_emulator.py
   ````
3. **Запуск эмулятора**:
    
    ````
    python shell_emulator.py config.ini`
    ````
## Примеры использования

**Запуск эмулятора:**
````
python shell_emulator.py config.ini Убрана не нужная по условию команда echo в описании

````
 **Пример сеанса работы:**

 С помощью ручного ввода рассмотрим как работают команды в эмуляторе
 
![image](https://github.com/user-attachments/assets/6c118898-3b27-49e1-bfdf-fd60a62d3a86)

В результате видим во время прогна всех необходимых команд в одной сессии, все они корректно выполняют свою работу

## Результаты прогонов тестов

**Тестовый файл для прогона всех комманд (на каждую комманду покрытие в 2 теста)**
````
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

````
Запуск тестов с помощью ```unittest```:
````
python test_shell_emulator.py
````

**Вывод**:

````
Launching unittests with arguments python -m unittest C:\Users\korot\PycharmProjects\ShellEmulator\pythonProject\test_shell_emulator.py in C:\Users\korot\PycharmProjects\ShellEmulator\pythonProject



Ran 16 tests in 0.185s

OK
````
Все тесты успешно пройдены, что подтверждает корректность работы всех функций эмулятора и поддерживаемых команд.

