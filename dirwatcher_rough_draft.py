import asyncio
import os
import signal
import logging
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

logging.basicConfig(filename="dirwatcher_rough.log", level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(name)s:%(message)s')


async def stream_handler(*, time: int = 3, magic_string: str = "cat", directory: str = os.getcwd()) -> "async generator coroutine":
    """receives files and directories to be consumed"""

    with os.scandir(directory) as d:
        file_bank_initial = [f.name for f in d if os.path.isfile(f)]

    while True:

        output = yield
        if not output:
            continue

        elif os.path.isdir(output):
            # print(os.path.basename(output))

            pass

            # print("directory")
            # head, tail = os.path.split(output)
            # print(f"{head=}")
            # print(f"{tail=}")

        elif os.path.isfile(output) and output.endswith(".txt"):

            with os.scandir(directory) as direct:
                file_bank_current = [
                    f.name for f in direct if os.path.isfile(f)]

            f = os.path.basename(output)
            print(f)

            is_added = f not in file_bank_initial and f in file_bank_current

            # for item in file_bank_current:
            if is_added:
                print(f"file: {f} added")
                file_bank_initial.append(f)

            for z in file_bank_initial:
                is_removed = z not in file_bank_current
                if is_removed:
                    print(f"file: {z} removed")
                    file_bank_initial = [
                        item for item in file_bank_initial if item != z]

        #############################################################

            logger.info(f)
            # print(os.path.basename(output))
            with open(f) as fil:
                lines = fil.read().splitlines()
                # print(lines)
            for line_numb, line in enumerate(lines):
                if magic_string in line:
                    print(
                        f"Found: {magic_string} in File:{f} on line {line_numb}")
                    logger.info(
                        f"Found: {magic_string} in File:{f} on line {line_numb}")

        else:
            pass
            # await asyncio.sleep(1)


async def infiniteloop1(*, time: int = 3) -> None:
    """Initiates an infinite loop that creates a stream of files and directors to be consumed"""
    # await asyncio.sleep(1)
    x = stream_handler()
    await x.asend(None)

    while True:
        print("starting")
        with os.scandir(os.getcwd()) as d:

            for f in d:
                await x.asend(f.__fspath__())

            try:
                while q := next(d):
                    await x.asend(q)

            except StopIteration:
                continue
            finally:
                print("ended cycle")
                await asyncio.sleep(time)


def exit_program(sig: str, loop: str, /) ->None:
    """receives os signal and handles int and term and ends the loop"""
    print(f"\nReceived {sig}: exiting...")

    loop.stop()


async def main():
    logger.info(f"Started at {(time:=datetime.datetime.now())}")
    logger.info(f"{(pid:=os.getpid())=}")
    loop = asyncio.get_running_loop()
    sig_names = {"SIGINT", "SIGTERM"}

    for sig_name in sig_names:
        logger.info(f"Signals: {getattr(signal, sig_name)}")
        loop.add_signal_handler(getattr(signal, sig_name),
                                exit_program, sig_name, loop)

    task1 = asyncio.create_task(infiniteloop1())

    await task1

if __name__ == "__main__":
    try:
        asyncio.run(main(), debug=True)
    except RuntimeError:
        print("exited program")
