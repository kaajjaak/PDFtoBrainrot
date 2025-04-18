import cv2
import json
import os
import pysrt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile
import subprocess
from pathlib import Path

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
    
    def get_text_dimensions(self, text, font):
        """Get text dimensions using PIL."""
        text_image = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(text_image)
        return draw.textbbox((0, 0), text, font=font)
    
    def create_text_image(self, text, width, height, font_size=70):
        """Create an image with text using PIL."""
        # Try to use ProximaNova-Semibold if available, otherwise use a default font
        try:
            font = ImageFont.truetype("ProximaNova-Semibold.ttf", font_size)
        except IOError:
            # Use a default font if ProximaNova is not available
            font = ImageFont.load_default()
            font_size = 40  # Adjust default font size
        
        # Create a transparent image
        text_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_image)
        
        # Wrap text if needed
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self.get_text_dimensions(test_line, font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= width - 40:  # Leave some margin
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate text height
        line_height = font_size * 1.2
        text_height = len(lines) * line_height
        
        # Calculate vertical position to center the text
        y_position = (height - text_height) // 2
        
        # Draw text with stroke (outline)
        for line in lines:
            bbox = self.get_text_dimensions(line, font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            
            # Draw stroke (outline)
            for dx, dy in [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]:
                draw.text((x_position + dx, y_position + dy), line, font=font, fill=(0, 0, 0, 255))
            
            # Draw text
            draw.text((x_position, y_position), line, font=font, fill=(255, 255, 255, 255))
            y_position += line_height
        
        return np.array(text_image)
    
    def process_video(self, video_path, audio_path, srt_path, output_path):
        try:
            # Load progress
            start_time = self.load_progress(video_path)
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Get audio duration using ffprobe
            audio_duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
            ]
            audio_duration = float(subprocess.check_output(audio_duration_cmd).decode('utf-8').strip())
            
            # Calculate start frame
            start_frame = int(start_time * fps)
            
            # Set position to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Calculate end frame based on audio duration
            end_frame = start_frame + int(audio_duration * fps)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create temporary video file (without audio)
            temp_video_path = os.path.join(tempfile.gettempdir(), "temp_video.mp4")
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'avc1' for h264 codec
            out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
            
            # Load subtitles
            subs = pysrt.open(srt_path)
            
            # Process frames
            current_frame_idx = start_frame
            
            while current_frame_idx < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert frame to RGBA for overlay
                frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                
                # Check if there's a subtitle for this frame
                current_time = (current_frame_idx - start_frame) / fps
                
                for sub in subs:
                    start_sub_time = sub.start.ordinal / 1000
                    end_sub_time = sub.end.ordinal / 1000
                    
                    if start_sub_time <= current_time < end_sub_time:
                        # Create subtitle image
                        subtitle_img = self.create_text_image(sub.text, width, height)
                        
                        # Overlay subtitle on frame
                        alpha_s = subtitle_img[:, :, 3] / 255.0
                        alpha_l = 1.0 - alpha_s
                        
                        for c in range(0, 3):
                            frame_rgba[:, :, c] = (alpha_s * subtitle_img[:, :, c] + 
                                                alpha_l * frame_rgba[:, :, c])
                        
                        break
                
                # Convert back to BGR for writing
                frame_bgr = cv2.cvtColor(frame_rgba, cv2.COLOR_BGRA2BGR)
                
                # Write frame
                out.write(frame_bgr)
                current_frame_idx += 1
            
            # Release video resources
            cap.release()
            out.release()
            
            # Combine video with audio using ffmpeg
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', temp_video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            
            # Update progress
            self.save_progress(video_path, start_time + audio_duration)
            
            # Clean up temporary file
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            return output_path
            
        except Exception as e:
            # Clean up resources in case of error
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            if 'out' in locals():
                out.release()
            if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            raise RuntimeError(f"Error processing video: {str(e)}")
