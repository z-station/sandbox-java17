import os
import re
import uuid
import shutil
from collections import namedtuple
from app import config

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))


def detect_class_name(code: str) -> str:
    match = re.search(r'public\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    match = re.search(r'class\s+(\w+)', code)
    if match:
        return match.group(1)
    return 'Main'


class JavaFile:

    """ Описывает файлы, необходимые для запуска программы """

    def __init__(self, code: str):
        file_id = uuid.uuid4()
        self.class_name = detect_class_name(code)
        self.work_dir = os.path.join(config.SANDBOX_DIR, str(file_id))
        os.makedirs(self.work_dir, mode=0o777, exist_ok=True)
        self.filepath_java = os.path.join(
            self.work_dir, f'{self.class_name}.java'
        )
        with open(self.filepath_java, 'w') as file:
            file.write(code)

    def remove(self):
        try:
            shutil.rmtree(self.work_dir)
        except:
            pass
