import asyncio
import os
import signal
import functools
import argparse
import logging

logger = logging.getLogger(__name__)


async def hello(time, /):
    while True:
        print("hello")
        await asyncio.sleep(time)


async def goodbye(time, /):
    while True:
        print("goodbye")
        await asyncio.sleep(time)


def exit_program(sig, loop):

    logger.warning(f"Received {sig}: exiting...")

    loop.stop()


async def file_generator(*, directory: str = os.getcwd(), time: int = 3):
    while True:

        with os.scandir(directory) as d:
            for entry in d:
                yield d
                await asyncio.sleep(time)


async def directory_aseembler():
    files = file_generator()
    async for file in files:
        print(next(file))


def namespace():
    description = "Searches for *Magic Word* in a file directory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-p", "--polling",
                        help="sets polling interval", default=5, type=int)
    parser.add_argument("-d", "--directory")
    return parser.parse_args()


async def main():
    args = namespace()
    polling = args.polling

    loop = asyncio.get_running_loop()
    task1 = asyncio.create_task(hello(polling))
    task2 = asyncio.create_task(goodbye(polling))
    task3 = asyncio.create_task(directory_aseembler())
    print("main is running...")
    print(os.getpid())
    sig_names = {"SIGINT", "SIGTERM"}

    # files = file_generator()
    for sig_name in sig_names:
        print(getattr(signal, sig_name))
        loop.add_signal_handler(
            getattr(signal, sig_name), exit_program, sig_name, loop)

    # async for file in files:
    #     print(next(file))

    await task1, task2, task3


if __name__ == "__main__":
    try:
        asyncio.run(main(), debug=True)
    except RuntimeError:
        print("exited program")
