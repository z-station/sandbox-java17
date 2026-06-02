import re
from typing import Optional
from app import messages


INPUT_ERROR_PATTERNS = (
    'java.util.NoSuchElementException',
    'java.util.InputMismatchException',
    'java.lang.NumberFormatException',
)

TIMEOUT_PATTERNS = (
    'Terminated',
    'timed out',
)


def clean_str(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        return value.replace('\r', '').rstrip('\n')
    return value


def clean_error(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        value = clean_str(value)

        value = re.sub(
            pattern=r'\/(tmp|sandbox)(?:\/\S+)*\/\S*\.java',
            repl='Main.java',
            string=value
        )

        if any(x in value for x in TIMEOUT_PATTERNS):
            value = messages.MSG_1

        elif any(x in value for x in INPUT_ERROR_PATTERNS):
            value = messages.MSG_8

        elif 'the monitored command dumped core' in value:
            value = clean_str(
                re.sub(
                    pattern=r'(?im)^.*the monitored command dumped core.*$',
                    repl='',
                    string=value
                )
            )

    return value or None
