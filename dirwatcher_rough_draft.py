import asyncio
import os
import signal


async def something():

    while True:
        output = yield
        if not output:
            continue
            # await asyncio.sleep(1)
        elif os.path.isdir(output):
            # print("directory")
            print(os.path.basename(output))
            # head, tail = os.path.split(output)
            # print(f"{head=}")
            # print(f"{tail=}")
            await asyncio.sleep(1)
        elif os.path.isfile(output):
            # print("is file")
            # print(output)
            print(os.path.basename(output))
            await asyncio.sleep(1)
        else:

            print(output)

        # time.sleep(1)
        await asyncio.sleep(1)


async def infiniteloop1():

    x = something()
    await x.asend(None)

    while True:
        print("starting")
        with os.scandir(os.getcwd()) as d:

            for f in d:
                await x.asend(f.__fspath__())
                # time.sleep(1)

            try:
                while q := next(d):
                    await x.asend(q)
                # time.sleep(1)

            except StopIteration:
                continue
            finally:
                print("ended cycle")
                # time.sleep(1)
                await asyncio.sleep(1)


def exit_program(sig, loop):

    print(f"Received {sig}: exiting...")

    loop.stop()
    # os.kill(os.getpid(), signal.SIGINT)


async def main():
    print("main is running...")
    print(os.getpid())
    loop = asyncio.get_running_loop()
    sig_names = {"SIGINT", "SIGTERM"}

    for sig_name in sig_names:
        print(getattr(signal, sig_name))
        loop.add_signal_handler(getattr(signal, sig_name),
                                exit_program, sig_name, loop)

    task1 = asyncio.create_task(infiniteloop1())

    await task1

if __name__ == "__main__":
    try:
        asyncio.run(main(), debug=True)
    except RuntimeError:
        print("exited program")
