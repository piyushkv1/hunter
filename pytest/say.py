import asyncio


async def say(what, when):
    await asyncio.sleep(when)
    return what


async def main():
    print(await say('what', 3))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())