import os
import cv2
import numpy as np


def edit_video(input_file, output_file):
    try:
        # Load video
        cap = cv2.VideoCapture(input_file)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        if duration <= 20:  # If video is too short
            print(f"Video {input_file} is too short to edit")
            cap.release()
            return
        
        # Calculate start frame (skip first 10 seconds)
        start_time = 10
        start_frame = int(start_time * fps)
        
        # Calculate crop dimensions for TikTok aspect ratio (9:16)
        target_width = height * 9 // 16
        x1 = (width - target_width) // 2
        x2 = x1 + target_width
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'avc1' for h264 codec
        out = cv2.VideoWriter(output_file, fourcc, fps, (target_width, height))
        
        # Set position to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Process frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Crop frame
            cropped_frame = frame[:, x1:x2]
            
            # Write frame to output
            out.write(cropped_frame)
        
        # Release resources
        cap.release()
        out.release()
        
        print(f"Successfully edited: {output_file}")
    except Exception as e:
        print(f"Failed to edit {input_file}: {str(e)}")
        # Release resources in case of exception
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        if 'out' in locals():
            out.release()


if __name__ == "__main__":
    INPUT_FILE = r".\downloads\parkour2.mp4"  # Specify the input file path here
    OUTPUT_FILE = "../videos/minecraft/minecraft_01.mp4"  # Specify the output file path here

    print("Starting video editing process...")
    edit_video(INPUT_FILE, OUTPUT_FILE)
