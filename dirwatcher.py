import asyncio
import os
import signal
import logging
import datetime
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
filename = "dirwatcher.log"
logging.basicConfig(filename=filename, level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(name)s:%(message)s')


def namespace(func: callable) -> callable:
    description = "Searches for *Magic Word* in a file directory"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("magic", help="choose a magic string to watch")
    parser.add_argument("-p", "--polling", metavar="",
                        help="sets polling interval", default=5, type=int)
    parser.add_argument("-d", "--directory", type=str, metavar="",
                        help="choose directory to watch", default=os.getcwd())
    parser.add_argument("-e", "--extension", default=".txt",
                        help="choose file extension to monitor in directory")

    args = parser.parse_args()

    polling = args.polling
    directory = args.directory
    magic_string = args.magic
    extension = args.extension

    return lambda: func(polling=polling, directory=directory, extension=extension, magic_string=magic_string)


@namespace
async def stream_handler(directory: str, magic_string: str, extension: str, **kwargs) -> "async generator coroutine":
    """receives files and directories to be consumed"""
    magic_cache = {}

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
                # is_removed = z not in file_bank_current

                if (is_removed := z not in file_bank_current):
                    logger.info(f"file: {z} removed")
                    file_bank_initial = [
                        item for item in file_bank_initial if item != z]
                    print(f"before: {magic_cache}")
                    magic_cache = {k: v for k,
                                   v in magic_cache.items() if k != z}
                    print(f"after: {magic_cache}")

            with open(output) as fil:
                lines = fil.read().splitlines()

            for line_numb, line in enumerate(lines):
                with open("dirwatcher.log") as dir_log:
                    log_lines = dir_log.read()

                if magic_string in line:
                    magic_cache.setdefault(f, [])
                    # print(f"magic= {magic_cache[f]}")

                    if (line_numb) not in magic_cache[f]:
                        magic_cache[f].append((line_numb))

                        # if f"Found: {magic_string} in File:{f} on line {line_numb + 1}" not in log_lines:
                        #     logger.info(
                        #         f"Found: {magic_string} in File:{f} on line {line_numb + 1}")
                        logger.info(
                            f"Found:{magic_string} in File:{f} on line: {line_numb+1}")


@namespace
async def infiniteloop(polling, directory, **kwargs) -> None:
    """Initiates an infinite loop that creates a stream of files and directors to be consumed"""
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
            continue
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
    """searches for magic text and monitors files being added or removed in a directory"""
    print("watching...")
    logger.info("Started")
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
