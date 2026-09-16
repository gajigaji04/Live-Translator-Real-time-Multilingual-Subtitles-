import json

import websockets


class CaptionServer:

    def __init__(
        self,
        host: str,
        port: int,
    ):
        self.host = host
        self.port = port

        self.clients = set()

    async def handler(
        self,
        websocket,
    ):
        self.clients.add(websocket)

        print(
            f"[WebSocket] Client connected "
            f"({len(self.clients)})"
        )

        try:

            await websocket.wait_closed()

        finally:

            self.clients.discard(websocket)

            print(
                f"[WebSocket] Client disconnected "
                f"({len(self.clients)})"
            )

    async def start(self):

        await websockets.serve(
            self.handler,
            self.host,
            self.port,
        )

        print(
            f"WebSocket server: "
            f"ws://{self.host}:{self.port}"
        )

    async def broadcast(
        self,
        data: dict,
    ):

        if not self.clients:
            return

        message = json.dumps(
            data,
            ensure_ascii=False,
        )

        disconnected = set()

        for client in self.clients:

            try:

                await client.send(
                    message
                )

            except Exception as error:

                print(
                    "[WebSocket] Send error:",
                    error,
                )

                disconnected.add(client)

        for client in disconnected:

            self.clients.discard(
                client
            )