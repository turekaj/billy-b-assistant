"""Test mode audio support - mock microphone input and OpenAI Realtime API."""

import asyncio
import json
import time
import threading
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
import numpy as np

from .logger import logger


@dataclass
class MockAudioChunk:
    """Represents an audio chunk that would be played to speakers."""
    timestamp: float
    duration: float
    sample_rate: int
    channels: int
    audio_bytes: bytes


class MockMicManager:
    """Mock microphone manager for test mode audio input."""

    def __init__(self, sample_rate=24000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_running = False
        self.callback = None
        self.thread = None
        self._stop_event = threading.Event()

    def start(self, callback: Callable[[np.ndarray], None]) -> None:
        """Start mock microphone, calling callback with audio frames."""
        if self.is_running:
            return

        self.callback = callback
        self.is_running = True
        self._stop_event.clear()

        # Optionally, start a thread that calls the callback with silence
        # This keeps the microphone "active" in test mode
        self.thread = threading.Thread(target=self._mic_thread, daemon=True)
        self.thread.start()

        logger.info("Mock microphone started (test mode)", "🎤")

    def stop(self) -> None:
        """Stop mock microphone."""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()

        if self.thread:
            self.thread.join(timeout=2.0)

        logger.info("Mock microphone stopped", "🎤")

    def _mic_thread(self) -> None:
        """Background thread that keeps microphone "active" by sending silence."""
        while not self._stop_event.is_set():
            if self.callback and self.is_running:
                # Send a chunk of silence periodically
                silence = np.zeros(self.sample_rate // 25, dtype=np.float32)  # 40ms of silence
                try:
                    self.callback(silence)
                except Exception as e:
                    logger.warning(f"Error in mock mic callback: {e}")

            time.sleep(0.04)  # 40ms chunks

    def inject_audio(self, audio_data: np.ndarray) -> None:
        """Inject audio data into the microphone stream (for testing voice input)."""
        if not self.is_running or not self.callback:
            return

        try:
            self.callback(audio_data)
        except Exception as e:
            logger.warning(f"Error injecting audio to mic: {e}")


class MockOpenAIWebSocket:
    """Mock WebSocket for OpenAI Realtime API in test mode."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.response_queue: asyncio.Queue = asyncio.Queue()
        self.is_connected = True
        self._message_index = 0
        self._default_responses = []

    async def send(self, message: str | bytes) -> None:
        """Send a message to the mock API."""
        if isinstance(message, bytes):
            message = message.decode('utf-8')

        try:
            msg_data = json.loads(message)
            self.sent_messages.append(msg_data)

            # Log important message types
            msg_type = msg_data.get('type', 'unknown')
            if msg_type == 'input_audio_buffer.append':
                logger.verbose("Mock API received audio chunk", "🎤")
            elif msg_type == 'input_audio_buffer.commit':
                logger.verbose("Mock API: audio chunk committed", "✅")
            elif msg_type == 'response.create':
                logger.verbose("Mock API: response create requested", "🤖")
        except json.JSONDecodeError:
            pass

    async def recv(self) -> str:
        """Receive a message from the mock API."""
        # Return queued responses, or empty string if none
        try:
            return await asyncio.wait_for(self.response_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            # Return heartbeat to keep connection alive
            return json.dumps({"type": "session.updated"})

    def queue_response(self, response: Dict[str, Any]) -> None:
        """Queue a response to be returned by recv()."""
        try:
            self.response_queue.put_nowait(json.dumps(response))
        except asyncio.QueueFull:
            pass

    def queue_audio_response(self, audio_base64: str, transcript: str = "") -> None:
        """Queue an audio response from the AI."""
        # Audio delta response
        self.queue_response({
            "type": "response.audio_transcript.delta",
            "delta": transcript
        })

        self.queue_response({
            "type": "response.output_audio.delta",
            "index": self._message_index,
            "delta": audio_base64
        })

        self._message_index += 1

        # Mark response as done
        self.queue_response({
            "type": "response.done",
            "response": {
                "status": "completed",
                "output": [{"type": "audio", "audio": audio_base64}]
            }
        })

    async def close(self) -> None:
        """Close the mock WebSocket."""
        self.is_connected = False
        logger.info("Mock WebSocket closed", "🔌")

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Get all messages sent to the mock API."""
        return self.sent_messages.copy()

    def get_audio_messages(self) -> List[Dict[str, Any]]:
        """Get all audio input messages sent."""
        return [m for m in self.sent_messages if m.get('type') == 'input_audio_buffer.append']


class TestAudioCapture:
    """Capture audio that would be played to speakers in test mode."""

    def __init__(self):
        self.captured_chunks: List[MockAudioChunk] = []
        self._lock = threading.Lock()
        self.capture_enabled = True

    def capture_chunk(self, audio_bytes: bytes, sample_rate: int = 48000,
                     channels: int = 2, duration: float = None) -> None:
        """Capture an audio chunk that would be played."""
        if not self.capture_enabled:
            return

        if duration is None:
            # Estimate duration from byte length
            bytes_per_frame = channels * 2  # 16-bit = 2 bytes
            num_frames = len(audio_bytes) // bytes_per_frame
            duration = num_frames / sample_rate

        chunk = MockAudioChunk(
            timestamp=time.time(),
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            audio_bytes=audio_bytes
        )

        with self._lock:
            self.captured_chunks.append(chunk)

        logger.verbose(f"Captured audio chunk: {duration:.3f}s at {sample_rate}Hz", "🎙️")

    def get_captured_audio(self) -> List[MockAudioChunk]:
        """Get all captured audio chunks."""
        with self._lock:
            return self.captured_chunks.copy()

    def get_total_duration(self) -> float:
        """Get total duration of captured audio."""
        with self._lock:
            return sum(chunk.duration for chunk in self.captured_chunks)

    def clear(self) -> None:
        """Clear captured audio."""
        with self._lock:
            self.captured_chunks.clear()


# Global test audio instances
_test_mic_manager: Optional[MockMicManager] = None
_test_websocket: Optional[MockOpenAIWebSocket] = None
_test_audio_capture: Optional[TestAudioCapture] = None


def get_test_mic_manager() -> MockMicManager:
    """Get or create the test microphone manager."""
    global _test_mic_manager
    if _test_mic_manager is None:
        _test_mic_manager = MockMicManager()
    return _test_mic_manager


def get_test_websocket() -> MockOpenAIWebSocket:
    """Get or create the test WebSocket."""
    global _test_websocket
    if _test_websocket is None:
        _test_websocket = MockOpenAIWebSocket()
    return _test_websocket


def get_test_audio_capture() -> TestAudioCapture:
    """Get or create the test audio capture."""
    global _test_audio_capture
    if _test_audio_capture is None:
        _test_audio_capture = TestAudioCapture()
    return _test_audio_capture


def reset_test_audio() -> None:
    """Reset all test audio components (for test cleanup)."""
    global _test_mic_manager, _test_websocket, _test_audio_capture

    if _test_mic_manager:
        _test_mic_manager.stop()
    if _test_audio_capture:
        _test_audio_capture.clear()

    _test_mic_manager = None
    _test_websocket = None
    _test_audio_capture = None


def get_test_audio_status() -> dict:
    """Get status of test audio system.

    Note: These metrics show status of MOCK systems (for fully automated testing).
    When using real hardware (microphone, API, speakers), these show as 0/inactive.
    Check server logs for real hardware activity (Mic Volume, Billy responses, etc.)
    """
    mic = get_test_mic_manager()
    ws = get_test_websocket()
    capture = get_test_audio_capture()

    return {
        "mode": "Real hardware (microphone, API, speakers) - not using mock systems",
        "mock_mic_running": mic.is_running,
        "mock_websocket_connected": ws.is_connected,
        "mock_audio_messages_sent": len(ws.get_audio_messages()),
        "mock_audio_chunks_captured": len(capture.get_captured_audio()),
        "mock_total_captured_duration": capture.get_total_duration()
    }
