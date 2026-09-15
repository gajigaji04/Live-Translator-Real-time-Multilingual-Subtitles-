import aiohttp

from openai import AsyncOpenAI

from app.config import (
    TRANSLATION_PROVIDER,
    DEEPL_API_KEY,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


LANGUAGE_NAMES = {
    "KO": "Korean",
    "EN": "English",
    "JA": "Japanese",
    "ZH": "Chinese",
}


class Translator:

    def __init__(self, target_language: str):

        self.target_language = target_language.upper()

        if TRANSLATION_PROVIDER == "openai":

            self.client = AsyncOpenAI(
                api_key=OPENAI_API_KEY
            )

    async def translate(
        self,
        text: str,
        source_language: str | None = None
    ):

        if not text:
            return ""

        if (
            source_language
            and source_language.upper()
            == self.target_language
        ):
            return text

        if TRANSLATION_PROVIDER == "deepl":
            return await self._deepl(
                text,
                source_language
            )

        if TRANSLATION_PROVIDER == "openai":
            return await self._openai(
                text,
                source_language
            )

        raise ValueError(
            f"Unknown translation provider: "
            f"{TRANSLATION_PROVIDER}"
        )

    async def _deepl(
        self,
        text: str,
        source_language: str | None
    ):

        url = "https://api-free.deepl.com/v2/translate"

        data = {
            "text": text,
            "target_lang": self.target_language,
        }

        if source_language:
            data["source_lang"] = source_language.upper()

        headers = {
            "Authorization":
                f"DeepL-Auth-Key {DEEPL_API_KEY}"
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                data=data,
                headers=headers,
            ) as response:

                if response.status != 200:

                    body = await response.text()

                    raise RuntimeError(
                        f"DeepL error: "
                        f"{response.status} {body}"
                    )

                result = await response.json()

                return result[
                    "translations"
                ][0]["text"]

    async def _openai(
        self,
        text: str,
        source_language: str | None
    ):

        target = LANGUAGE_NAMES.get(
            self.target_language,
            self.target_language
        )

        source = (
            LANGUAGE_NAMES.get(
                source_language.upper()
            )
            if source_language
            else "unknown"
        )

        response = await self.client.chat.completions.create(

            model=OPENAI_MODEL,

            temperature=0,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a real-time subtitle "
                        "translator. "
                        "Translate naturally and concisely. "
                        "Return only the translated text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Source language: {source}\n"
                        f"Target language: {target}\n\n"
                        f"{text}"
                    ),
                },
            ],
        )

        return response.choices[0].message.content.strip()