import asyncio
import base64
import json
import numpy as np
import websockets.asyncio.client
from typing import Optional, Dict, Any, List

from ..realtime_ai_provider import RealtimeAIProvider
from ..config import XAI_API_KEY


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

    async def generate_audio_clip(self, prompt: str, voice: Optional[str] = None, instructions: Optional[str] = None, **kwargs) -> bytes:
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
            session_instructions = (
                "IMPORTANT: Always respond by speaking the exact user text out loud. Do not add, change or rephrase anything!"
            )
            if instructions:
                session_instructions += "\n\n" + instructions

            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "instructions": session_instructions,
                    "voice": voice,
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm", "rate": 16000},
                        },
                        "output": {
                            "format": {"type": "audio/pcm", "rate": 16000},
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
                raise RuntimeError("No audio data received from XAI.")

            return bytes(audio_bytes)

    def get_supported_voices(self) -> list[str]:
        return ["Rex", "Ara", "Sal", "Eve", "Leo"]

    def get_supported_models(self) -> list[str]:
        return ["grok-realtime"]  # Assuming this is the model name

    def get_provider_name(self) -> str:
        return "xai"

    @property
    def default_voice(self) -> str:
        return "Sal"

    # Conversation methods
    def get_websocket_uri(self, model: Optional[str] = None) -> str:
        return "wss://api.x.ai/v1/realtime"

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
                "format": {"type": "audio/pcm", "rate": 16000},
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
                "format": {"type": "audio/pcm", "rate": 16000},
                "voice": voice,
            }

        return {
            "type": "session.update",
            "session": {
                "instructions": instructions,
                "voice": voice,
                "turn_detection": {
                    "type": "server_vad",
                },
                "audio": audio_config,
                "tools": tools,
            },
        }

    def get_provider_tools(self) -> List[Dict]:
        # XAI doesn't have provider-specific tools beyond the base ones
        return []

    def handle_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # For XAI, handle function calls like in the user's example
        event_type = event.get("type", "")

        if event_type == "response.function_call_arguments.done":
            # This would be handled by the conversation handler
            # Return the event to be processed
            return event

        # For other events, no special handling needed
        return event