import asyncio
import json
import websockets


class CaptionServer:

    def __init__(
        self,
        host: str,
        port: int
    ):

        self.host = host
        self.port = port

        self.clients = set()

    async def handler(
        self,
        websocket
    ):

        self.clients.add(websocket)

        print(
            "Client connected:",
            websocket.remote_address
        )

        try:

            await websocket.wait_closed()

        finally:

            self.clients.discard(websocket)

    async def broadcast(
        self,
        data: dict
    ):

        if not self.clients:
            return

        message = json.dumps(
            data,
            ensure_ascii=False
        )

        await asyncio.gather(
            *[
                client.send(message)
                for client in self.clients
            ],
            return_exceptions=True
        )

    async def start(self):

        print(
            f"WebSocket server: "
            f"ws://{self.host}:{self.port}"
        )

        return await websockets.serve(
            self.handler,
            self.host,
            self.port,
        )