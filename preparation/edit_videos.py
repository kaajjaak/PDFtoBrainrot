import os
from moviepy.editor import VideoFileClip
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def edit_video(input_file, output_file):
    try:
        # Load video
        clip = VideoFileClip(input_file)

        # Get video duration and calculate middle section
        duration = clip.duration
        if duration <= 20:  # If video is too short
            print(f"Video {input_file} is too short to edit")
            return

        # Cut off the first 10 seconds and keep the rest
        start_time = 10
        trimmed_clip = clip.subclip(start_time)

        # Crop to TikTok aspect ratio (9:16)
        width, height = trimmed_clip.size
        target_width = height * 9 // 16
        x1 = (width - target_width) // 2
        cropped_clip = trimmed_clip.crop(x1=x1, x2=x1 + target_width)

        # Remove audio
        final_clip = cropped_clip.without_audio()

        # Write the final video
        final_clip.write_videofile(
            output_file,
            codec="libx264",
            audio=False,
            preset='ultrafast'
        )

        print(f"Successfully edited: {output_file}")
    except Exception as e:
        print(f"Failed to edit {input_file}: {str(e)}")
    finally:
        # Ensure all clips are closed even if an error occurs
        if 'clip' in locals(): clip.close()
        if 'trimmed_clip' in locals(): trimmed_clip.close()
        if 'cropped_clip' in locals(): cropped_clip.close()
        if 'final_clip' in locals(): final_clip.close()


if __name__ == "__main__":
    INPUT_FILE = r".\downloads\Over an Hour of clean Minecraft Parkour (No Falls, Full Daytime, Download in description).mp4"  # Specify the input file path here
    OUTPUT_FILE = "../videos/minecraft/minecraft_02.mp4"  # Specify the output file path here

    print("Starting video editing process...")
    edit_video(INPUT_FILE, OUTPUT_FILE)
