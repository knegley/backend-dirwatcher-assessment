import asyncio
import os
import signal
import functools
import argparse
import logging
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

logging.basicConfig(filename="dirwatcher.log", level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(name)s:%(message)s')

line_handler = logging.FileHandler("dirwatcher.log")
logger.addHandler(line_handler)


async def hello(time, /):
    while True:
        logger.info("hello")
        await asyncio.sleep(time)


async def goodbye(time, /):
    while True:
        logger.info("goodbye")
        await asyncio.sleep(time)


def exit_program(sig, loop):

    logger.warning(f"Received {sig}: exiting...")

    loop.stop()


async def file_generator(*, directory: str = os.getcwd(), time: int = 3):
    while True:
        with os.scandir(directory) as d:
            for entry in d:
                print(f"file_generator: {entry}")

                yield d
                await asyncio.sleep(time)


async def directory_assembler():

    files = file_generator()
    try:
        async for file in files:
            # print(next(file))
            # print(next(file).name)
            # print(dir(next(file)))
            # print(f"file ={files}")
            yield(next(file).__fspath__())
            await asyncio.sleep(1)
    except StopIteration:
        os.kill(os.getpid(), signal.SIGINT)


async def line_assembler():

    paths = directory_assembler()

    try:
        async for path in paths:

            print(f"line assembler: {path}")

            if os.path.isfile(path) and path != "/mnt/c/Users/Kyle Negley/Documents/GitHub/backend-dirwatcher-assessment/dirwatcher.py":
                with open(path) as f:
                    lines = (f.read().splitlines())
                # print(lines)
                logger.info(lines)
                yield(lines)
                await asyncio.sleep(1)
    except StopIteration:
        print("exhausted")
        os.kill(os.getpid(), signal.SIGINT)


async def iterate_lines():
    lines = line_assembler()

    # while True:

    try:
        async for line in lines:
            print("logging lines...")
            # print(line)
            await asyncio.sleep(1)
    except StopIteration:
        print("iterating lines exhausted")
        os.kill(os.getpid(), signal.SIGINT)

        # else:
        #     iterate_lines()


def namespace():
    description = "Searches for *Magic Word* in a file directory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-p", "--polling",
                        help="sets polling interval", default=5, type=int)
    parser.add_argument("-d", "--directory")
    return parser.parse_args()


async def main():
    time = datetime.datetime.now()
    print(f"Started: {time}")
    args = namespace()
    polling = args.polling

    loop = asyncio.get_running_loop()
    task1 = asyncio.create_task(hello(polling))
    task2 = asyncio.create_task(goodbye(polling))
    # task3 = asyncio.create_task(directory_assembler())
    # task4 = asyncio.create_task(line_assembler())
    task5 = asyncio.create_task(iterate_lines())
    print("main is running...")
    print(f"PID={os.getpid()}")
    sig_names = {"SIGINT", "SIGTERM"}

    # files = file_generator()
    for sig_name in sig_names:
        # logger.info(getattr(signal, sig_name))
        loop.add_signal_handler(
            getattr(signal, sig_name), exit_program, sig_name, loop)

    await task1, task2, task5


if __name__ == "__main__":
    time = datetime.datetime.now()
    try:
        asyncio.run(main(), debug=True)
    except RuntimeError:
        print(f"exited program at {time}")
