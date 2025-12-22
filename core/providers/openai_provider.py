import asyncio
import base64
import json
import websockets.asyncio.client
from typing import Optional, Dict, Any, List

from ..realtime_ai_provider import RealtimeAIProvider
from ..config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIProvider(RealtimeAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-realtime-mini", voice: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        if voice and voice in self.get_supported_voices():
            self.voice = voice
        else:
            self.voice = "alloy"  # Provider's default

    @property
    def default_voice(self) -> str:
        return self.voice

    async def generate_audio_clip(self, prompt: str, voice: Optional[str] = None, instructions: Optional[str] = None, **kwargs) -> bytes:
        if voice is None:
            voice = self.default_voice
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        async with websockets.asyncio.client.connect(
            uri, additional_headers=headers
        ) as ws:
            # Send session update
            session_instructions = (
                "IMPORTANT: Always respond by speaking the exact user text out loud. Do not add, change or rephrase anything!"
            )
            if instructions:
                session_instructions += "\n\n" + instructions

            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": session_instructions,
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm", "rate": 24000},
                        },
                        "output": {
                            "format": {"type": "audio/pcm", "rate": 24000},
                            "voice": voice,
                        },
                    },
                },
            }))

            # Send conversation item
            await ws.send(json.dumps({
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
            }))

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
                raise RuntimeError("No audio data received from OpenAI.")

            return bytes(audio_bytes)

    def get_supported_voices(self) -> list[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def get_provider_name(self) -> str:
        return "openai"

    @property
    def default_voice(self) -> str:
        return "alloy"

    # Conversation methods
    def get_websocket_uri(self) -> str:
        return f"wss://api.openai.com/v1/realtime?model={self.model}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    def get_initial_session_config(self, instructions: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        server_vad_params = kwargs.get("server_vad_params", {})
        text_only_mode = kwargs.get("text_only_mode", False)
        voice = kwargs.get("voice", self.default_voice)

        audio_config = {
            "input": {
                "format": {"type": "audio/pcm", "rate": 24000},
                "turn_detection": {
                    "type": "server_vad",
                    **server_vad_params,
                    "create_response": True,
                    "interrupt_response": True,
                },
            },
        }

        if not text_only_mode:
            audio_config["output"] = {
                "format": {"type": "audio/pcm", "rate": 24000},
                "voice": voice,
                "speed": 1.0,
            }

        return {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": instructions,
                "tools": tools,
                "audio": audio_config,
            },
        }

    def get_provider_tools(self) -> List[Dict]:
        # OpenAI doesn't have provider-specific tools beyond the base ones
        return []

    def handle_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # For OpenAI, no special event handling needed yet
        # Could be extended for provider-specific event processing
        return event