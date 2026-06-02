# Тесты запускать только в контейнере!
import pytest
import subprocess
from unittest.mock import call
from app.service.main import JavaService
from app import config, messages
from app.entities import (
    DebugData,
    TestsData,
    TestData
)
from app.service.entities import ExecuteResult
from app.service.entities import JavaFile
from app.service.exceptions import CheckerException
from app.service import exceptions


def test_execute__console_result__ok():

    data_in = '2 3'
    code = (
        'import java.util.Scanner;\n'
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '        Scanner sc = new Scanner(System.in);\n'
        '        int a = sc.nextInt();\n'
        '        int b = sc.nextInt();\n'
        '        System.out.println(a + b);\n'
        '    }\n'
        '}\n'
    )
    file = JavaFile(code)
    JavaService._compile(file)

    exec_result = JavaService._execute(file=file, data_in=data_in)

    assert exec_result.result == '5'
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_integer__ok():

    data_in = (
        '6\n'
        '50'
    )
    code = (
        'import java.util.Scanner;\n'
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '        Scanner sc = new Scanner(System.in);\n'
        '        int n = sc.nextInt();\n'
        '        int k = sc.nextInt();\n'
        '        System.out.println(k / n);\n'
        '        System.out.println(k - (k / n) * n);\n'
        '    }\n'
        '}\n'
    )
    file = JavaFile(code)
    JavaService._compile(file)

    exec_result = JavaService._execute(file=file, data_in=data_in)

    assert exec_result.result == (
        '8\n'
        '2'
    )
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():

    code = (
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '    }\n'
        '}\n'
    )
    file = JavaFile(code)
    JavaService._compile(file)

    exec_result = JavaService._execute(file=file)

    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__timeout__return_error(mocker):

    code = (
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '        while (true) {}\n'
        '    }\n'
        '}\n'
    )
    file = JavaFile(code)
    JavaService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    execute_result = JavaService._execute(file=file)

    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__write_access__error():

    """ Тест работает только в контейнере
        т.к. там ограничены права на запись в файловую систему """

    code = (
        'import java.nio.file.*;\n'
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '        if (Files.isWritable(Paths.get("/app/src"))) {\n'
        '            System.out.println("Write allowed.");\n'
        '        } else {\n'
        '            System.out.println("Write Permission denied.");\n'
        '        }\n'
        '    }\n'
        '}\n'
    )
    file = JavaFile(code)
    JavaService._compile(file)

    exec_result = JavaService._execute(file=file)

    assert 'Write Permission denied.' in exec_result.result
    assert exec_result.error is None
    file.remove()


def test_execute__clear_error_message__ok(mocker):

    raw_error_message = (
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff/Main.java:2: "
        "error: cannot find symbol\n"
        "        adqeqwd\n"
        "        ^\n"
        "  symbol:   variable adqeqwd\n"
        "  location: class Main\n"
    )
    clear_error_message = (
        "Main.java:2: "
        "error: cannot find symbol\n"
        "        adqeqwd\n"
        "        ^\n"
        "  symbol:   variable adqeqwd\n"
        "  location: class Main"
    )
    code = 'public class Main { public static void main(String[] args) {} }'
    file = JavaFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, raw_error_message)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    exec_result = JavaService._execute(file=file)

    communicate_mock.assert_called_once_with(
        input=None,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    assert exec_result.result is None
    assert exec_result.error == clear_error_message
    file.remove()


def test_execute__proc_exception__raise_exception(mocker):

    code = 'public class Main { public static void main(String[] args) {} }'
    data_in = 'Some data in'
    file = JavaFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception()
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    with pytest.raises(exceptions.ExecutionException) as ex:
        JavaService._execute(file=file, data_in=data_in)

    assert ex.value.message == messages.MSG_6
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    file.remove()


def test_compile__timeout__error(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=subprocess.TimeoutExpired(cmd='', timeout=config.TIMEOUT)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    error = JavaService._compile(file_mock)

    assert error == messages.MSG_1
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__exception__raise_exception(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    with pytest.raises(exceptions.CompileException) as ex:
        JavaService._compile(file_mock)

    assert ex.value.message == messages.MSG_7
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__error__error(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, compile_error)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    error = JavaService._compile(file_mock)

    assert error == compile_error
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__ok(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, None)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    JavaService._compile(file_mock)

    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_check__true__ok():

    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    check_result = JavaService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    assert check_result is True


def test_check__false__ok():

    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    check_result = JavaService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    assert check_result is False


def test_check__invalid_checker_func__raise_exception():

    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        JavaService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():

    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  result = right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        JavaService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():

    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return None'
    )

    with pytest.raises(CheckerException) as ex:
        JavaService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():

    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  include(invalid syntax here)'
        '  return True'
    )

    with pytest.raises(CheckerException) as ex:
        JavaService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    assert ex.value.message == messages.MSG_5
    assert ex.value.details == 'invalid syntax. Perhaps you forgot a comma? (<string>, line 1)'


def test_debug__compile_is_success__ok(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.JavaService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.JavaService._execute',
        return_value=execute_result
    )
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    debug_result = JavaService.debug(data)

    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in
    )
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):

    compile_error = 'some error'
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.JavaService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.JavaService._execute')
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    debug_result = JavaService.debug(data)

    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.JavaService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.JavaService._execute',
        return_value=execute_result
    )
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.JavaService._check',
        return_value=check_result
    )
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    testing_result = JavaService.testing(data)

    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list == [
        call(
            file=file_mock,
            data_in=test_1.data_in
        ),
        call(
            file=file_mock,
            data_in=test_2.data_in
        )
    ]
    assert check_mock.call_args_list == [
        call(
            checker_func=data.checker,
            right_value=test_1.data_out,
            value=execute_result.result
        ),
        call(
            checker_func=data.checker,
            right_value=test_2.data_out,
            value=execute_result.result
        )
    ]
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):

    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    compile_mock = mocker.patch(
        'app.service.main.JavaService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.JavaService._execute')
    check_mock = mocker.patch('app.service.main.JavaService._check')
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    testing_result = JavaService.testing(data)

    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result is None
    assert tests_result[0].error == compile_error
    assert tests_result[0].ok is False
    assert tests_result[1].result is None
    assert tests_result[1].error == compile_error
    assert tests_result[1].ok is False
