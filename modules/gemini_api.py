import os
import json
from dotenv import load_dotenv
import google.generativeai as genai


class PDFProcessor:
    def __init__(self, cache_file="pdf_cache.json"):
        load_dotenv()
        print("Initializing PDFProcessor...")
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=self.api_key)
        self.assistant_name = "TikTok Script Generator"
        self.cache_file = cache_file
        self.file_cache = self.load_cache()
        print("Initialization complete.")

    def load_cache(self):
        """Load the cache from a JSON file."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        """Save the cache to a JSON file."""
        with open(self.cache_file, "w") as f:
            json.dump(self.file_cache, f)

    def upload_file(self, file_path):
        """Upload the PDF file to Gemini."""
        file_name = os.path.basename(file_path)

        if file_name in self.file_cache:
            print(f"Using cached file: {file_name}")
            return self.file_cache[file_name]

        try:
            print(f"\nUploading file: {file_name}")
            uploaded_file = genai.upload_file(path=file_path, display_name=file_name)
            self.file_cache[file_name] = uploaded_file.uri
            self.save_cache()
            print(f"File uploaded successfully: {uploaded_file.display_name}")
            return uploaded_file.uri
        except Exception as e:
            raise RuntimeError(f"Failed to upload file: {e}")

    def process_pdf(self, pdf_path, prompt_text):
        """Process the PDF and generate a response using Gemini."""
        try:
            print("\n" + "=" * 50)
            print(f"Starting processing of PDF: {os.path.basename(pdf_path)}")
            print("=" * 50)

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

            pdf_uri = self.upload_file(pdf_path)

            model_name = "models/gemini-1.5-flash"
            prompt = {
                "role": "user",
                "parts": [
                    {"file_data": {"file_uri": pdf_uri, "mime_type": "application/pdf"}},
                    {"text": prompt_text}
                ]
            }

            print("\nGenerating content...")
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content(
                contents=[prompt],
                request_options={"timeout": 600}
            )

            if response.text:
                print("Response generated successfully!")
                return response.text

            print("No response generated.")
            return "No response generated."

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            raise RuntimeError(f"Failed to process PDF: {str(e)}")
