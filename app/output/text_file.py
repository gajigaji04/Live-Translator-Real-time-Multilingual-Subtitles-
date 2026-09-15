import asyncio


class TextFileOutput:

    def __init__(self, filename: str):

        self.filename = filename

    async def write(
        self,
        text: str
    ):

        await asyncio.to_thread(
            self._write_sync,
            text
        )

    def _write_sync(
        self,
        text: str
    ):

        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)