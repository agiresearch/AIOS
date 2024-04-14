import os
import sys

def find_pytest_main(path):
    """
    Recursively searches through the given path to find the __main__.py file
    inside the pytest folder, and returns the absolute path if found.
    """
    if os.path.isdir(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and item == 'pytest':
                main_path = os.path.join(item_path, '__main__.py')
                if os.path.exists(main_path):
                    return main_path
            else:
                result = find_pytest_main(item_path)
                if result:
                    return result
    return None

def add_import_to_file(file_path, import_line):
    with open(file_path, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(import_line.rstrip('\r\n') + '\n' + content)

if __name__ == '__main__':
    python_exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    pytest_main_path = find_pytest_main(python_exec_dir)

    import_line = "from src.llms.llm_config import LLMMeta"

    add_import_to_file(pytest_main_path, import_line)
