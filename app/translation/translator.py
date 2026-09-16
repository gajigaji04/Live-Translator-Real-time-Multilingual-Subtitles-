import aiohttp

from app.config import (
    TRANSLATION_PROVIDER,
    DEEPL_API_KEY,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


class Translator:

    def __init__(self):
        self.provider = (
            TRANSLATION_PROVIDER.lower()
        )

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:

        if not text.strip():
            return ""

        # 같은 언어면 번역하지 않는다.
        if (
            source_language.lower()
            == target_language.lower()
        ):
            return text

        if self.provider == "deepl":
            return await self._deepl(
                text,
                source_language,
                target_language,
            )

        if self.provider == "openai":
            return await self._openai(
                text,
                source_language,
                target_language,
            )

        raise ValueError(
            f"Unknown translation provider: "
            f"{self.provider}"
        )

    # =========================
    # DeepL
    # =========================

    async def _deepl(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:

        if not DEEPL_API_KEY:
            raise RuntimeError(
                "DEEPL_API_KEY is not configured."
            )

        url = (
            "https://api-free.deepl.com/v2/translate"
        )

        headers = {
            "Authorization":
                f"DeepL-Auth-Key {DEEPL_API_KEY}",
            "Content-Type":
                "application/x-www-form-urlencoded",
        }

        data = {
            "text": text,
            "target_lang":
                target_language.upper(),
        }

        if source_language:
            data["source_lang"] = (
                source_language.upper()
            )

        timeout = aiohttp.ClientTimeout(
            total=10
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(
                url,
                headers=headers,
                data=data,
            ) as response:

                if response.status != 200:

                    body = await response.text()

                    raise RuntimeError(
                        f"DeepL error: "
                        f"{response.status} "
                        f"{body}"
                    )

                result = await response.json()

                translations = result.get(
                    "translations",
                    [],
                )

                if not translations:
                    return ""

                return translations[0].get(
                    "text",
                    "",
                )

    # =========================
    # OpenAI
    # =========================

    async def _openai(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:

        if not OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        url = (
            "https://api.openai.com/v1/chat/completions"
        )

        headers = {
            "Authorization":
                f"Bearer {OPENAI_API_KEY}",
            "Content-Type":
                "application/json",
        }

        prompt = (
            f"Translate the following text from "
            f"{source_language} to "
            f"{target_language}.\n\n"
            f"Return only the translation.\n\n"
            f"Text:\n{text}"
        )

        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
        }

        timeout = aiohttp.ClientTimeout(
            total=10
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(
                url,
                headers=headers,
                json=payload,
            ) as response:

                if response.status != 200:

                    body = await response.text()

                    raise RuntimeError(
                        f"OpenAI error: "
                        f"{response.status} "
                        f"{body}"
                    )

                result = await response.json()

                return (
                    result["choices"][0]
                    ["message"]["content"]
                    .strip()
                )