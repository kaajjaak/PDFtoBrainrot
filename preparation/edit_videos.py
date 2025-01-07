import cv2
import os
from datetime import datetime


def get_duration_str(frame_count, fps):
    duration_sec = frame_count / fps
    return f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s"


def edit_videos(input_dir, output_dir):
    # Verify directories
    global cap, out
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist!")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Get list of MP4 files
    mp4_files = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]
    if not mp4_files:
        print(f"No MP4 files found in '{input_dir}'")
        return

    print(f"Found {len(mp4_files)} MP4 files to process")

    for file_name in mp4_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, f"edited_{file_name}")

        print(f"\nProcessing: {file_name}")
        start_time = datetime.now()

        try:
            # Open video file
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                print(f"Failed to open video: {input_path}")
                continue

            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            print(f"Video properties:")
            print(f"- Duration: {get_duration_str(frame_count, fps)}")
            print(f"- FPS: {fps}")
            print(f"- Resolution: {width}x{height}")

            # Calculate frame positions
            start_frame = fps * 10  # Skip first 10 seconds
            middle_start = int(frame_count * 0.25)
            middle_end = int(frame_count * 0.75)

            # Calculate dimensions for TikTok aspect ratio (9:16)
            target_width = int(height * 9 / 16)
            x_start = int((width - target_width) / 2)

            # Try different codecs
            codecs = ['mp4v', 'XVID', 'MJPG']
            out = None

            for codec in codecs:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    temp_output = output_path if codec == 'mp4v' else output_path.replace('.mp4', '.avi')
                    out = cv2.VideoWriter(temp_output, fourcc, fps, (target_width, height))
                    if out.isOpened():
                        print(f"Using codec: {codec}")
                        break
                except Exception as e:
                    print(f"Codec {codec} failed, trying next...")
                    if out is not None:
                        out.release()

            if out is None or not out.isOpened():
                raise Exception("Could not initialize video writer with any codec")

            frame_num = 0
            frames_to_process = middle_end - middle_start
            processed_frames = 0
            last_progress = -1

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_num >= start_frame and middle_start <= frame_num <= middle_end:
                    # Crop to center for TikTok aspect ratio
                    cropped = frame[:, x_start:x_start + target_width]

                    if cropped.shape[1] == target_width and cropped.shape[0] == height:
                        out.write(cropped)
                        processed_frames += 1

                        # Update progress every 5%
                        progress = int((processed_frames / frames_to_process) * 100)
                        if progress % 5 == 0 and progress != last_progress:
                            elapsed_time = datetime.now() - start_time
                            print(f"Progress: {progress}% (Time elapsed: {elapsed_time})")
                            last_progress = progress

                frame_num += 1

            # Release resources
            cap.release()
            out.release()

            total_time = datetime.now() - start_time
            print(f"Successfully edited: {output_path}")
            print(f"Total processing time: {total_time}")

        except Exception as e:
            print(f"Failed to edit {file_name}: {str(e)}")
            if 'cap' in locals(): cap.release()
            if 'out' in locals() and out is not None: out.release()


if __name__ == "__main__":
    INPUT_FOLDER = "downloads"
    OUTPUT_FOLDER = "../videos/minecraft"

    print("Starting video editing process...")
    edit_videos(INPUT_FOLDER, OUTPUT_FOLDER)
