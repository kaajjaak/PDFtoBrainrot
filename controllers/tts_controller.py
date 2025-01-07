import os
from modules.tts_converter import PollyTTS


class TTSController:
    def __init__(self):
        self.tts_converter = PollyTTS()

    def process_script(self, script_path):
        """Process a script file to generate audio and subtitles."""
        try:
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script file not found: {script_path}")

            print(f"Processing script: {os.path.basename(script_path)}")

            # Convert script to audio and generate subtitles
            result = self.tts_converter.convert_script_to_audio(script_path)

            print(f"Successfully generated:")
            print(f"- Audio: {result['audio_path']}")
            print(f"- Subtitles: {result['subtitle_path']}")

            return result

        except Exception as e:
            print(f"Failed to process script: {str(e)}")
            raise

