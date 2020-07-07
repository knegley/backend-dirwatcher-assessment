import asyncio
import os
import signal
import logging
import datetime
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

logging.basicConfig(filename="dirwatcher_rough.log", level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(name)s:%(message)s')


def namespace(func):
    description = "Searches for *Magic Word* in a file directory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("magic", help="choose a magic string to watch")
    parser.add_argument("-p", "--polling",
                        help="sets polling interval", default=5, type=int)
    parser.add_argument("-d", "--directory", type=str,
                        help="choose directory to watch", default=os.getcwd())
    parser.add_argument("-e", "--extension", default=".txt",
                        help="choose file extension to monitor in directory")

    args = parser.parse_args()

    polling = args.polling
    directory = args.directory
    magic_string = args.magic
    extension = args.extension
    # print(directory)
    # print(magic_string)
    return lambda: func(polling=polling, directory=directory, extension=extension, magic_string=magic_string)


@namespace
async def stream_handler(directory: str, magic_string: str, extension: str, **kwargs) -> "async generator coroutine":
    """receives files and directories to be consumed"""

    try:

        with os.scandir(directory) as d:
            file_bank_initial = [f.name for f in d if os.path.isfile(f)]
    except FileNotFoundError as e:
        logger.exception(e)

    except NotADirectoryError as ex:
        logger.exception(ex)

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

        elif os.path.isfile(output) and output.endswith(extension):

            with os.scandir(directory) as direct:
                file_bank_current = [
                    f.name for f in direct if os.path.isfile(f)]

            f = os.path.basename(output)
            # print(f"file : {f}")

            is_added = f not in file_bank_initial and f in file_bank_current

            # for item in file_bank_current:
            if is_added:
                # print(f"file: {f} added")
                logger.info(f"file: {f} added")
                file_bank_initial.append(f)

            for z in file_bank_initial:
                is_removed = z not in file_bank_current
                if is_removed:
                    # print(f"file: {z} removed")
                    logger.info(f"file: {z} removed")
                    file_bank_initial = [
                        item for item in file_bank_initial if item != z]

        #############################################################

            # logger.info(f)
            # print(os.path.basename(output))
            with open(output) as fil:
                lines = fil.read().splitlines()
                # print(lines)
            for line_numb, line in enumerate(lines):
                with open("dirwatcher_rough.log") as dir_log:
                    log_lines = dir_log.read()
                if magic_string in line:

                    if f"Found: {magic_string} in File:{f} on line {line_numb}" not in log_lines:
                        logger.info(
                            f"Found: {magic_string} in File:{f} on line {line_numb}")

        else:
            pass
            # await asyncio.sleep(1)


@namespace
async def infiniteloop(polling, directory, **kwargs) -> None:
    """Initiates an infinite loop that creates a stream of files and directors to be consumed"""
    # await asyncio.sleep(1)
    x = stream_handler()
    await x.asend(None)

    while True:
        # print("starting")
        try:
            with os.scandir(directory) as d:

                for f in d:
                    await x.asend(f.__fspath__())

                while q := next(d):
                    await x.asend(q)
        except FileNotFoundError as e:
            continue

        except NotADirectoryError as ex:
            logger.exception(ex)

        except StopIteration:
            continue
        except StopAsyncIteration:
            continue
        finally:
            # print("ended cycle")
            await asyncio.sleep(polling)


def exit_program(sig: str, loop: str, /) ->None:
    """receives os signal and handles int and term and ends the loop"""
    logger.warning(f"Received {sig}: exiting...")

    loop.stop()


async def main():
    """searches for magic text and monitors files being added or removed in a directory"""
    print("watching...")
    logger.info("Started")
    # logger.info(f"Started at {(time:=datetime.datetime.now())}")
    logger.info(f"{(pid:=os.getpid())=}")
    loop = asyncio.get_running_loop()
    sig_names = {"SIGINT", "SIGTERM"}

    for sig_name in sig_names:
        logger.info(f"Signal to stop program: {getattr(signal, sig_name)}")
        loop.add_signal_handler(getattr(signal, sig_name),
                                exit_program, sig_name, loop)

    task1 = asyncio.create_task(infiniteloop())

    await task1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        logger.info("exited program")
