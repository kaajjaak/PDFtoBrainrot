from controllers.pdf_to_script_controller import convert_pdf_to_script
from controllers.tts_controller import TTSController
from controllers.video_controller import VideoController
import os
import time
import sys


def process_pdf_to_video(pdf_path):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Define all output paths
    script_path = os.path.join("scripts", f"{base_name}.json")
    audio_path = os.path.join("audio", f"{base_name}.mp3")
    srt_path = os.path.join("audio", "subtitles", f"{base_name}.srt")
    output_video_path = os.path.join("output", f"{base_name}_final.mp4")

    print(f"Processing PDF: {pdf_path}")

    # Step 1: Convert PDF to script
    print("\n== Converting PDF to Script ==")
    prompt_file = "prompts/brainrot.txt"
    convert_pdf_to_script(os.path.abspath(pdf_path), os.path.abspath(prompt_file))

    # Step 2: Process script through TTS
    print("\n== Converting Script to Audio ==")
    tts_controller = TTSController()
    try:
        result = tts_controller.process_script(script_path)
        print(f"Audio generated: {result['audio_path']}")
        print(f"Subtitles generated: {result['subtitle_path']}")
    except Exception as e:
        raise RuntimeError(f"TTS processing failed: {str(e)}")

    # Step 3: Create video
    print("\n== Creating Final Video ==")
    video_controller = VideoController()
    background_video_path = "videos/minecraft/edited_1 hour 22 minutes of relaxing Minecraft Parkour (60fps, Scenic, Download in the Description).mp4"

    if not os.path.exists(background_video_path):
        raise FileNotFoundError(f"Background video not found: {background_video_path}")

    try:
        final_video_path = video_controller.process_segment(
            os.path.abspath(background_video_path),
            os.path.abspath(audio_path),
            os.path.abspath(srt_path),
            os.path.abspath(output_video_path)
        )
        print(f"\nFinal video created successfully: {final_video_path}")
        return final_video_path

    except Exception as e:
        raise RuntimeError(f"Video processing failed: {str(e)}")


def cleanup_failed_outputs(base_name):
    """Clean up any partially created files from failed processing"""
    paths_to_cleanup = [
        os.path.join("scripts", f"{base_name}.json"),
        os.path.join("audio", f"{base_name}.mp3"),
        os.path.join("audio", "subtitles", f"{base_name}.srt"),
        os.path.join("output", f"{base_name}_final.mp4")
    ]

    for path in paths_to_cleanup:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Cleaned up: {path}")
            except Exception as e:
                print(f"Failed to clean up {path}: {str(e)}")


def main():
    # Create necessary directories
    for directory in ["input", "scripts", "audio", os.path.join("audio", "subtitles"), "output"]:
        os.makedirs(directory, exist_ok=True)

    input_folder = "input"
    processed_files = []
    max_retries = 3
    retry_delay = 5  # seconds

    # Process all PDF files in input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, filename)
            base_name = os.path.splitext(filename)[0]

            print(f"\n{'=' * 50}")
            print(f"Processing {filename}")
            print(f"{'=' * 50}")

            retries = 0
            while retries < max_retries:
                try:
                    output_path = process_pdf_to_video(pdf_path)
                    processed_files.append((filename, output_path))
                    print(f"\n== Successfully processed {filename} ==")
                    break

                except Exception as e:
                    retries += 1
                    print(f"\nError processing {filename} (Attempt {retries}/{max_retries}): {str(e)}")

                    if retries < max_retries:
                        print(f"Cleaning up failed outputs and retrying in {retry_delay} seconds...")
                        cleanup_failed_outputs(base_name)
                        time.sleep(retry_delay)
                    else:
                        print(f"\nMax retries reached for {filename}. Stopping program.")
                        print("\nFiles processed before failure:")
                        for proc_file, out_path in processed_files:
                            print(f"- {proc_file} -> {out_path}")
                        sys.exit(1)


if __name__ == "__main__":
    main()
