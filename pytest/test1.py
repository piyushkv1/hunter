import asyncio
import pytest

from say import say

#  Solution : 1
#  Drawback : every test that want to execute coroutine is required to
#  submitted to event loop
@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


def test_say(event_loop):
    expected = 'Helloo!'
    assert expected == event_loop.run_until_complete(say('Hello!', 0))


# # Solution : 2
# # Using asyncio plugin
# @pytest.mark.asyncio
# async def test_say():
#     print("HELLOWORLDS")
#     assert 'Hello!' == await say('Hello!', 0)
