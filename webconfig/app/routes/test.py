"""Test mode API endpoints."""

from flask import Blueprint, request, jsonify
from core import test_mode
from core.logger import logger

test_bp = Blueprint("test", __name__, url_prefix="/test")


@test_bp.route("/status", methods=["GET"])
def get_test_status():
    """Get current test mode status."""
    return jsonify(test_mode.get_test_status())


@test_bp.route("/button", methods=["POST"])
def trigger_button():
    """Trigger virtual button press (for testing)."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        test_mode.trigger_virtual_button()
        return jsonify({"success": True, "message": "Virtual button triggered"})
    except Exception as e:
        logger.error(f"Error triggering virtual button: {e}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/motor-log", methods=["GET"])
def get_motor_log():
    """Get all logged motor events."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    return jsonify({
        "motor_events": test_mode.get_motor_log(),
        "count": len(test_mode.get_motor_log())
    })


@test_bp.route("/motor-log/clear", methods=["POST"])
def clear_motor_log():
    """Clear motor log."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    test_mode.clear_motor_log()
    return jsonify({"success": True, "message": "Motor log cleared"})


@test_bp.route("/motor-log/download", methods=["GET"])
def download_motor_log():
    """Download motor log as JSON."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    from flask import send_file
    import io
    import json

    log_data = json.dumps(test_mode.get_motor_log(), indent=2)
    return send_file(
        io.BytesIO(log_data.encode()),
        mimetype="application/json",
        as_attachment=True,
        download_name="motor_log.json"
    )


@test_bp.route("/mode/enable", methods=["POST"])
def enable_test_mode():
    """Enable test mode (if not already enabled)."""
    if test_mode.is_test_mode_enabled():
        return jsonify({
            "success": True,
            "message": "Test mode already enabled"
        })

    test_mode.enable_test_mode()
    return jsonify({
        "success": True,
        "message": "Test mode enabled"
    })


@test_bp.route("/audio/status", methods=["GET"])
def get_audio_status():
    """Get test mode audio status (microphone, API, captured audio)."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        from core import test_audio
        status = test_audio.get_test_audio_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting audio status: {e}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/audio/captured", methods=["GET"])
def get_captured_audio():
    """Get list of audio chunks captured during session."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        from core import test_audio
        capture = test_audio.get_test_audio_capture()
        chunks = capture.get_captured_audio()

        return jsonify({
            "chunks_count": len(chunks),
            "total_duration": capture.get_total_duration(),
            "chunks": [
                {
                    "timestamp": chunk.timestamp,
                    "duration": chunk.duration,
                    "sample_rate": chunk.sample_rate,
                    "channels": chunk.channels,
                    "size_bytes": len(chunk.audio_bytes)
                }
                for chunk in chunks
            ]
        })
    except Exception as e:
        logger.error(f"Error getting captured audio: {e}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/audio/api-messages", methods=["GET"])
def get_api_messages():
    """Get messages sent to OpenAI API during session."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        from core import test_audio
        ws = test_audio.get_test_websocket()
        messages = ws.get_sent_messages()

        return jsonify({
            "total_messages": len(messages),
            "audio_chunks": len(ws.get_audio_messages()),
            "messages": messages[:50]  # Return last 50 for brevity
        })
    except Exception as e:
        logger.error(f"Error getting API messages: {e}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/audio/captured/clear", methods=["POST"])
def clear_captured_audio():
    """Clear captured audio log."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        from core import test_audio
        test_audio.get_test_audio_capture().clear()
        return jsonify({"success": True, "message": "Captured audio cleared"})
    except Exception as e:
        logger.error(f"Error clearing captured audio: {e}")
        return jsonify({"error": str(e)}), 500


@test_bp.route("/audio/inject", methods=["POST"])
def inject_test_audio():
    """Inject test audio data into the mock microphone."""
    if not test_mode.is_test_mode_enabled():
        return jsonify({"error": "Test mode not enabled"}), 400

    try:
        import numpy as np
        from core import test_audio

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Get audio data - can be a list of floats or base64 encoded
        audio_data = data.get("audio")
        if not audio_data:
            return jsonify({"error": "Missing 'audio' field"}), 400

        # Convert to numpy array if it's a list
        if isinstance(audio_data, list):
            audio_array = np.array(audio_data, dtype=np.float32)
        else:
            # Try to decode as base64
            import base64
            audio_bytes = base64.b64decode(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)

        # Inject into mock microphone
        mic = test_audio.get_test_mic_manager()
        if mic and mic.is_running:
            mic.inject_audio(audio_array)
            return jsonify({
                "success": True,
                "message": f"Injected {len(audio_array)} audio samples",
                "samples_count": len(audio_array)
            })
        else:
            return jsonify({
                "error": "Mock microphone not running",
                "mic_running": mic.is_running if mic else False
            }), 400

    except Exception as e:
        logger.error(f"Error injecting audio: {e}")
        return jsonify({"error": str(e)}), 500
