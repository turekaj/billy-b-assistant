import asyncio
import base64
import json
import websockets.asyncio.client
from typing import Optional, Dict, Any, List

from ..realtime_ai_provider import RealtimeAIProvider


class XAIProvider(RealtimeAIProvider):
    def __init__(self, api_key: str, voice: Optional[str] = None):
        self.api_key = api_key
        if voice and voice in self.get_supported_voices():
            self.voice = voice
        else:
            self.voice = "Sal"  # Provider's default

    @property
    def default_voice(self) -> str:
        return self.voice

    async def generate_audio_clip(
        self,
        prompt: str,
        voice: Optional[str] = None,
        instructions: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        if voice is None:
            voice = self.default_voice
        uri = "wss://api.x.ai/v1/realtime"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        async with websockets.asyncio.client.connect(
            uri, additional_headers=headers
        ) as ws:
            # Send session update
            session_instructions = "IMPORTANT: Always respond by speaking the exact user text out loud. Do not add, change or rephrase anything!"
            if instructions:
                session_instructions += "\n\n" + instructions

            await ws.send(
                json.dumps({
                    "type": "session.update",
                    "session": {
                        "voice": voice,
                        "instructions": session_instructions,
                        "audio": {
                            "input": {
                                "format": {"type": "audio/pcm", "rate": 24000},
                            },
                            "output": {
                                "format": {"type": "audio/pcm", "rate": 24000},
                            },
                        },
                    },
                })
            )

            # Send conversation item
            await ws.send(
                json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Repeat this literal message:" + prompt,
                            }
                        ],
                    },
                })
            )

            # Create response
            await ws.send(json.dumps({"type": "response.create"}))

            # Collect audio
            audio_bytes = bytearray()
            async for message in ws:
                data = json.loads(message)
                t = data.get("type") or ""
                if t in {"response.output_audio", "response.output_audio.delta"}:
                    b64 = data.get("audio") or data.get("delta")
                    if b64:
                        audio_bytes.extend(base64.b64decode(b64))
                elif t == "response.done":
                    break

            if not audio_bytes:
                raise RuntimeError("No audio data received from XAI.")

            return bytes(audio_bytes)

    def get_supported_voices(self) -> list[str]:
        return ["Ara", "Rex", "Sal", "Eve", "Leo"]

    def get_connection_uri(self) -> str:
        return "wss://api.x.ai/v1/realtime"

    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def get_session_config(
        self,
        instructions: str,
        tools: Optional[list[dict[str, Any]]] = None,
        voice: Optional[str] = None,
        text_only: bool = False,
        vad_params: Optional[dict[str, Any]] = None,
    ) -> dict:
        all_tools = (tools or []) + [
            {
                "type": "web_search",
            },
            {
                "type": "x_search",
                "allowed_x_handles": ["elonmusk", "xai"],
            },
        ]

        return {
            "type": "session.update",
            "session": {
                "voice": voice,
                "instructions": instructions,
                "tools": all_tools,
                "turn_detection": {
                    "type": "server_vad",
                    "create_response": True,
                    "interrupt_response": True,
                    **(vad_params or {}),
                },
                "audio": {
                    "input": {"format": {"type": "audio/pcm", "rate": 24000}},
                    **(
                        {
                            "output": {"format": {"type": "audio/pcm", "rate": 24000}},
                        }
                        if not text_only
                        else {}
                    ),
                },
            },
        }

    def get_provider_name(self) -> str:
        return "xai"
