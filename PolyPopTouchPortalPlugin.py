import asyncio
import pip
import sqlite3

try:
    from loguru import logger
except ImportError:
    pip.main(['install', 'loguru'])
    from loguru import logger
finally:
    logger.add("debug.log", rotation='1 day')

try:
    import websockets
except ImportError:
    pip.main(['install', 'websockets'])
    import websockets

con = sqlite3.connect("con.db", check_same_thread=False)
clients = set()

try:
    con.execute("create table req(task, data)")
except sqlite3.OperationalError:
    pass


async def connect_client(websocket):
    global clients
    clients.add(websocket)
    logger.debug(f'Added client. Clients are now: {{{"".join(str(c.id) for c in clients)}, }}')
    await websocket.wait_closed()


async def handle_sdk():
    global clients
    global con
    await asyncio.create_subprocess_shell('PPWebSocketServer.py')
    while True:
        for task, data in con.execute("select task, data from req"):
            if task == 'message':
                for client in clients:
                    await client.send(data)
                con.execute('delete from req')
                con.commit()
            elif task == 'shutdown':
                for client in clients:
                    await client.close()
                break

        await asyncio.sleep(.01)


async def main():
    async with websockets.serve(connect_client, '127.0.0.1', 38031):
        await handle_sdk()


if __name__ == "__main__":
    asyncio.run(main())

