import os
import json
from modules.gemini_api import PDFProcessor


def convert_pdf_to_script(pdf_path, prompt_path):
    processed_path = None
    try:
        # Ensure folders exist
        processed_folder = "processed"
        scripts_folder = "scripts"
        os.makedirs(processed_folder, exist_ok=True)
        os.makedirs(scripts_folder, exist_ok=True)

        processed_path = os.path.join(processed_folder, os.path.basename(pdf_path))
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]

        # Read the prompt text
        with open(prompt_path, "r", encoding="utf8") as f:
            prompt_text = f.read()

        # Initialize processor and generate script
        print(f"Processing {pdf_path}...")
        processor = PDFProcessor()
        gpt_response = processor.process_pdf(pdf_path, prompt_text)

        # Remove code block markers if present
        if gpt_response.startswith("```"):
            gpt_response = gpt_response.replace("```json", "").replace("```", "")

        try:
            # Attempt to parse response as JSON
            gpt_json = json.loads(gpt_response)
            script_filename = f"{base_filename}.json"
            script_path = os.path.join(scripts_folder, script_filename)

            with open(script_path, "w", encoding="utf8") as f:
                json.dump(gpt_json, f, indent=4, ensure_ascii=False)
            print(f"Saved script as {script_filename}")

        except json.JSONDecodeError:
            script_filename = f"{base_filename}_response.txt"
            script_path = os.path.join(scripts_folder, script_filename)

            with open(script_path, "w", encoding="utf8") as f:
                f.write(gpt_response)
            print(f"Saved non-JSON response as {script_filename}")

        # Move processed PDF
        os.rename(pdf_path, processed_path)
        print(f"Moved {os.path.basename(pdf_path)} to processed folder")

    except Exception as e:
        print(f"Failed to process {pdf_path}: {e}")
        if processed_path and os.path.exists(processed_path):
            try:
                os.rename(processed_path, pdf_path)
            except Exception as restore_error:
                print(f"Failed to restore PDF file: {restore_error}")
