import asyncio
import os
import signal
import logging
import datetime
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(name)s:%(message)s')


def namespace(func: callable) -> callable:
    description = "Searches for *Magic Word* in a file directory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("magic_string", help="choose a magic string to watch")
    parser.add_argument("directory",
                        help="choose directory to watch")
    parser.add_argument("-p", "--polling", metavar="",
                        help="sets polling interval", default=5, type=int)
    parser.add_argument("-e", "--extension", default=".txt", metavar="",
                        help="choose file extension to monitor in directory")

    args = parser.parse_args()

    arguments = {arg: v for arg, v in args.__dict__.items()}

    return lambda: func(**arguments)


@namespace
# "async generator coroutine"
async def stream_handler(directory: str,
                         magic_string: str,
                         extension: str, polling: int, **kwargs) -> None:
    """receives files and directories to be consumed"""
    magic_cache = {}
    errors_bank = []
    while True:
        try:

            with os.scandir(directory) as d:
                file_bank_initial = [f.name for f in d if os.path.isfile(f)]

        except NotADirectoryError as ex:

            if ex.errno not in errors_bank:
                errors_bank.append(ex.errno)
                logger.exception(ex)

        except FileNotFoundError as e:
            if e.errno not in errors_bank:
                errors_bank.append(e.errno)
                logger.exception(e)

        finally:

            if os.path.isdir(directory):
                errors_bank = []
                break

            await asyncio.sleep(polling)

    while True:

        output = yield
        if not output:
            continue

        if os.path.isfile(output) and output.endswith(extension):

            with os.scandir(directory) as direct:
                file_bank_current = [
                    f.name for f in direct if os.path.isfile(f)]

            f = os.path.basename(output)

            is_added = f not in file_bank_initial and f in file_bank_current

            if is_added:
                logger.info(f"file: {f} added")
                file_bank_initial.append(f)

            for z in file_bank_initial:
                is_removed = z not in file_bank_current

                if (is_removed):
                    logger.info(f"file: {z} removed")
                    file_bank_initial = [
                        item for item in file_bank_initial if item != z]

                    magic_cache = {k: v for k,
                                   v in magic_cache.items() if k != z}

            with open(output) as fil:
                lines = fil.read().splitlines()

            for line_numb, line in enumerate(lines):
                found = f"Found:{magic_string} File:{f} line: {line_numb+1}"
                if magic_string in line:
                    magic_cache.setdefault(f, [])

                    if (line_numb) not in magic_cache[f]:
                        magic_cache[f].append((line_numb))

                        logger.info(found)


@namespace
async def infiniteloop(polling: int, directory: str, **kwargs) -> None:
    """Initiates an infinite loop that creates a stream of files and \
         directors to be consumed"""
    x = stream_handler()
    await x.asend(None)

    while True:
        try:
            with os.scandir(directory) as d:

                for f in d:
                    await x.asend(f.__fspath__())

                while q := next(d):
                    await x.asend(q)
        except FileNotFoundError as e:
            logger.exception(e)
        except NotADirectoryError as ex:
            logger.exception(ex)
        except StopIteration:
            continue
        except StopAsyncIteration:
            continue
        finally:

            await asyncio.sleep(polling)


def exit_program(sig: str, loop: str, /) ->None:
    """receives os signal and handles int and term and ends the loop"""
    logger.warning(f"Received {sig}: exiting...")
    loop.stop()


async def main():
    """searches for magic text and monitors files being added or \
        removed in a directory"""

    loop = asyncio.get_running_loop()
    sig_names = {"SIGINT", "SIGTERM"}

    for sig_name in sig_names:
        logger.info(f"Signal to stop program: {getattr(signal, sig_name)}")
        loop.add_signal_handler(getattr(signal, sig_name),
                                exit_program, sig_name, loop)

    task1 = asyncio.create_task(infiniteloop())

    await task1

if __name__ == "__main__":
    beginning = datetime.datetime.now()
    try:
        logger.info(f"\n{'*'*40}"
                    f"\nStarted: {beginning}\n"
                    f"Process: {os.getpid()}\n"
                    f"{'*'*40}\n")
        asyncio.run(main())
    except RuntimeError as e:
        logger.exception(e)
    finally:
        logger.info(f"\n{'*'*40}"
                    f"\nexited program\n"
                    f"Runtime: {datetime.datetime.now()-beginning}"
                    f"\n{'*'*40}")
