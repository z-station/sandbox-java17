import os
import shlex
from os import environ as env
from tempfile import gettempdir


"""
JAVA_OPTS:

-XX:+UseSerialGC
Включает Serial GC — однопоточный сборщик мусора.

По умолчанию в Java 17 часто стоит G1, которому нужно несколько потоков (GC Thread, concurrent mark и т.д.).
Serial GC использует один поток для сборки мусора — меньше нагрузка на лимиты nproc / pids в контейнере.
Минус: при больших объёмах памяти и долгих паузах GC может быть медленнее; для коротких sandbox-запусков
студенческого кода это обычно нормально.
+ в +UseSerialGC значит «включить»; -XX:-UseSerialGC было бы «выключить».
"""

TIMEOUT = 5  # seconds
SANDBOX_USER_UID = int(env.get('SANDBOX_USER_UID', os.getuid()))
SANDBOX_DIR = env.get('SANDBOX_DIR', gettempdir())

_DEFAULT_JAVA_OPTS = '-XX:+UseSerialGC'
JAVA_OPTS = shlex.split(env.get('JAVA_OPTS', _DEFAULT_JAVA_OPTS))
