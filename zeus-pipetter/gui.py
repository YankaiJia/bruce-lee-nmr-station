import asyncio
import time

async def print_hi():
    a = 0
    print('Hello ...')

    for i in range(100009000):
        a = i
    print('... World!')
    print(a)

async def print_hi2():
    b = 0
    print('Hello2 ...')
    for i in range(10900):
        b = i
    print('... World2!')
    print(b)


async def main():
    await asyncio.gather(print_hi(), print_hi2())

if __name__ == '__main__':

    asyncio.run(main())