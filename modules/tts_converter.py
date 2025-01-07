from datetime import timedelta
import boto3
import os
import json
import re
import time
from dotenv import load_dotenv


class PollyTTS:
    def __init__(self):
        load_dotenv()
        self.polly_client = boto3.client(
            'polly',
            region_name='eu-west-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.s3_client = boto3.client(
            's3',
            region_name='eu-west-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bucket_name = 'akina-brainrot'
        self.audio_folder = "audio"
        self.subtitles_folder = "audio/subtitles"
        os.makedirs(self.audio_folder, exist_ok=True)
        os.makedirs(self.subtitles_folder, exist_ok=True)

    def clean_text(self, text):
        """Remove markdown formatting and handle newlines."""
        text = text.replace('\\n\\n', '\n').replace('\\n', '\n')
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)

        sentences = text.split('\n')
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                if not sentence[-1] in '.!?':
                    sentence += '.'
                cleaned_sentences.append(sentence)

        return ' '.join(cleaned_sentences)

    def split_into_segments(self, text):
        """Split text into segments based on character count."""
        text = self.clean_text(text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        segments = []

        for sentence in sentences:
            if not sentence.strip():
                continue

            words = sentence.split()
            chunk = []
            chunk_length = 0

            for word in words:
                word_length = len(word)

                # If single word is longer than 12 chars, make it its own segment
                if word_length > 12:
                    if chunk:
                        segments.append(' '.join(chunk))
                    segments.append(word)
                    chunk = []
                    chunk_length = 0
                    continue

                # If adding this word would exceed 12 chars, start new segment
                if chunk_length + word_length + len(chunk) > 12:
                    segments.append(' '.join(chunk))
                    chunk = [word]
                    chunk_length = word_length
                else:
                    chunk.append(word)
                    chunk_length += word_length

            if chunk:
                segments.append(' '.join(chunk))

        return segments

    def parse_speech_marks(self, s3_key):
        """Get timing information from speech marks."""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        marks_data = response['Body'].read().decode('utf-8')

        marks = []
        for line in marks_data.strip().split('\n'):
            if line:
                marks.append(json.loads(line))

        return marks

    def convert_script_to_audio(self, script_path):
        try:
            print(f"Processing script: {script_path}")

            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)

            text = script_data.get('script', '')
            if not text:
                raise ValueError("No script text found in JSON")

            segments = self.split_into_segments(text)
            print(f"Split text into {len(segments)} segments")

            ssml_text = '<speak>'
            for i, segment in enumerate(segments):
                segment = segment.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                ssml_text += f'<mark name="segment_{i}"/>{segment} '
            ssml_text += '</speak>'

            base_name = os.path.splitext(os.path.basename(script_path))[0]
            s3_prefix = f"polly-output/{base_name}_{int(time.time())}"

            # Generate audio
            print("Starting speech synthesis task...")
            audio_response = self.polly_client.start_speech_synthesis_task(
                Text=ssml_text,
                TextType='ssml',
                OutputFormat='mp3',
                VoiceId='Matthew',
                Engine='neural',
                OutputS3BucketName=self.bucket_name,
                OutputS3KeyPrefix=s3_prefix
            )

            # Generate speech marks in parallel
            marks_response = self.polly_client.start_speech_synthesis_task(
                Text=ssml_text,
                TextType='ssml',
                OutputFormat='json',
                SpeechMarkTypes=['ssml', 'word'],
                VoiceId='Matthew',
                Engine='neural',
                OutputS3BucketName=self.bucket_name,
                OutputS3KeyPrefix=f"{s3_prefix}_marks"
            )

            # Wait for both tasks to complete
            audio_task_id = audio_response['SynthesisTask']['TaskId']
            marks_task_id = marks_response['SynthesisTask']['TaskId']

            while True:
                audio_status = self.polly_client.get_speech_synthesis_task(TaskId=audio_task_id)
                marks_status = self.polly_client.get_speech_synthesis_task(TaskId=marks_task_id)

                print(f"Audio status: {audio_status['SynthesisTask']['TaskStatus']}")
                print(f"Marks status: {marks_status['SynthesisTask']['TaskStatus']}")

                if (audio_status['SynthesisTask']['TaskStatus'] == 'completed' and
                        marks_status['SynthesisTask']['TaskStatus'] == 'completed'):
                    audio_uri = audio_status['SynthesisTask']['OutputUri']
                    marks_uri = marks_status['SynthesisTask']['OutputUri']
                    audio_key = audio_uri.split(self.bucket_name + '/')[1]
                    marks_key = marks_uri.split(self.bucket_name + '/')[1]
                    break
                elif any(status['SynthesisTask']['TaskStatus'] in ['failed', 'error']
                         for status in [audio_status, marks_status]):
                    raise Exception("Speech synthesis task failed")

                time.sleep(5)

            # Download files
            audio_path = os.path.join(self.audio_folder, f"{base_name}.mp3")
            srt_path = os.path.join(self.subtitles_folder, f"{base_name}.srt")

            print("Downloading audio file...")
            self.s3_client.download_file(self.bucket_name, audio_key, audio_path)

            # Generate SRT using speech marks
            print("Generating subtitles with accurate timing...")
            marks = self.parse_speech_marks(marks_key)

            # Separate word and SSML marks
            word_marks = [m for m in marks if m['type'] == 'word']
            ssml_marks = [m for m in marks if m['type'] == 'ssml']

            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                for i, segment in enumerate(segments, 1):
                    # Find start time from SSML mark
                    start_mark = next(m for m in ssml_marks if m['value'] == f'segment_{i - 1}')
                    start_time = timedelta(milliseconds=start_mark['time'])

                    # Find end time from next SSML mark or last word
                    if i < len(segments):
                        end_mark = next(m for m in ssml_marks if m['value'] == f'segment_{i}')
                        end_time = timedelta(milliseconds=end_mark['time'])
                    else:
                        # For last segment, use the time of the last word plus a buffer
                        last_word = word_marks[-1]
                        end_time = timedelta(milliseconds=last_word['time'] + 1000)

                    srt_file.write(f"{i}\n")
                    srt_file.write(
                        f"{str(start_time).replace('.', ',')[:11]} --> {str(end_time).replace('.', ',')[:11]}\n")
                    srt_file.write(f"{segment}\n\n")

            print("Processing completed successfully")
            return {
                'audio_path': audio_path,
                'subtitle_path': srt_path
            }

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            raise RuntimeError(f"Error converting script to audio: {str(e)}")
