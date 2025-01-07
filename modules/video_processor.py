from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import json
import os
import pysrt
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

class VideoProcessor:
    def __init__(self):
        self.progress_file = "progress.json"

    def load_progress(self, video_path):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                return progress.get(video_path, 0)
        return 0

    def save_progress(self, video_path, timestamp):
        progress = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
        progress[video_path] = timestamp
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f)

    def create_subtitle_clips(self, srt_path, video_size):
        subs = pysrt.open(srt_path)
        subtitle_clips = []
        for sub in subs:
            start_time = sub.start.ordinal / 1000
            end_time = sub.end.ordinal / 1000
            text_clip = (TextClip(sub.text,
                                font="ProximaNova-Semibold",
                                fontsize=70,
                                color='white',
                                stroke_color='black',
                                stroke_width=2,
                                size=(video_size[0]-40, None),
                                method='caption',
                                align='center')
                        .set_position(('center', 'center'))
                        .set_start(start_time)
                        .set_duration(end_time - start_time))
            subtitle_clips.append(text_clip)
        return subtitle_clips

    def process_video(self, video_path, audio_path, srt_path, output_path):
        try:
            start_time = self.load_progress(video_path)
            video = VideoFileClip(video_path).subclip(start_time)
            audio = AudioFileClip(audio_path)
            video = video.subclip(0, audio.duration)
            subtitle_clips = self.create_subtitle_clips(srt_path, video.size)
            final_video = CompositeVideoClip([video] + subtitle_clips)
            final_video = final_video.set_audio(audio.set_start(0))

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24
            )

            self.save_progress(video_path, start_time + audio.duration)

            video.close()
            audio.close()
            final_video.close()

            return output_path

        except Exception as e:
            raise RuntimeError(f"Error processing video: {str(e)}")
