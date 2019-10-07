import pytest


@pytest.fixture()
def param1():
    yield "param1"


@pytest.fixture()
def param2():
    yield "param2"


def fun1():
    assert 1 == 2, "Not equal"


class TestClass1():
    var = 1

    def test_1(self):
        print(self.var)
        self.var += 1

    def test_2(self):
        print(self.var)
        self.var += 1
        fun1()