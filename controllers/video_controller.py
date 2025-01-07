import os
from modules.video_processor import VideoProcessor

class VideoController:
    def __init__(self):
        self.processor = VideoProcessor()

    def process_segment(self, video_path, audio_path, srt_path, output_path):
        try:
            if not all(os.path.exists(p) for p in [video_path, audio_path, srt_path]):
                raise FileNotFoundError("One or more input files not found")

            print(f"Processing video segment...")
            print(f"Video: {video_path}")
            print(f"Audio: {audio_path}")
            print(f"Subtitles: {srt_path}")
            print(f"Output: {output_path}")

            result_path = self.processor.process_video(video_path, audio_path, srt_path, output_path)
            print(f"Successfully created video segment: {result_path}")

            return result_path

        except Exception as e:
            print(f"Failed to process video segment: {str(e)}")
            raise
