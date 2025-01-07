from openai import OpenAI
import os
from dotenv import load_dotenv
import time


class PDFProcessor:
    def __init__(self):
        load_dotenv()
        print("Initializing PDFProcessor...")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_name = "TikTok Script Generator"
        print("Initialization complete.")

    def get_or_create_assistant(self):
        """Get existing assistant or create a new one."""
        print("\nChecking for existing assistant...")
        for assistant in self.client.beta.assistants.list():
            if assistant.name == self.assistant_name:
                print(f"Found existing assistant: {assistant.id}")
                return assistant

        print("Creating new assistant...")
        assistant = self.client.beta.assistants.create(
            name=self.assistant_name,
            instructions="You are an assistant that generates TikTok scripts from PDFs.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}]
        )
        print(f"Created new assistant with ID: {assistant.id}")
        return assistant

    def get_existing_file(self, filename):
        """Check if file exists in OpenAI storage by filename."""
        print(f"\nChecking for existing file: {os.path.basename(filename)}")
        files = self.client.files.list()
        for file in files.data:
            if file.filename == os.path.basename(filename):
                print(f"Found existing file: {file.filename} (ID: {file.id})")
                return file
        print("File not found in storage.")
        return None

    def upload_file(self, file_path):
        """Upload file to OpenAI if it doesn't exist already."""
        existing_file = self.get_existing_file(file_path)
        if existing_file:
            print(f"Using existing file: {os.path.basename(file_path)} (ID: {existing_file.id})")
            return existing_file

        print(f"\nUploading new file: {os.path.basename(file_path)}")
        with open(file_path, "rb") as file:
            uploaded_file = self.client.files.create(
                file=file,
                purpose="assistants"
            )
            print(f"File uploaded successfully. ID: {uploaded_file.id}")
            return uploaded_file

    def process_pdf(self, pdf_path, prompt_text):
        """Process PDF and generate response."""
        try:
            print("\n" + "=" * 50)
            print(f"Starting processing of PDF: {os.path.basename(pdf_path)}")
            print("=" * 50)

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

            # Upload file if it doesn't exist
            uploaded_file = self.upload_file(pdf_path)

            # Get or create assistant
            assistant = self.get_or_create_assistant()

            # Create thread
            print("\nCreating new thread...")
            thread = self.client.beta.threads.create()
            print(f"Thread created with ID: {thread.id}")

            # Create message with file attachment
            print("\nAdding message to thread...")
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt_text,
                attachments=[{
                    "file_id": uploaded_file.id,
                    "tools": [{"type": "file_search"}]
                }]
            )
            print("Message added successfully")

            # Run assistant
            print("\nStarting assistant run...")
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="Generate a TikTok video script based on this PDF."
            )
            print(f"Run created with ID: {run.id}")

            # Wait for completion with timeout and better error handling
            max_retries = 30
            retry_count = 0

            print("\nWaiting for assistant to complete...")
            while retry_count < max_retries:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

                print(f"Run status: {run.status}")

                if run.status == "completed":
                    print("Run completed successfully!")
                    break
                elif run.status == "failed":
                    print("Run failed. Getting error details...")
                    print({
                        "status": run.status,
                        "last_error": getattr(run, "last_error", None),
                        "failed_at": getattr(run, "failed_at", None)
                    })
                    run_steps = self.client.beta.threads.runs.steps.list(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    error_details = [step.last_error for step in run_steps.data if hasattr(step, 'last_error')]
                    raise RuntimeError(f"Run failed with details: {error_details}")
                elif run.status in ["cancelled", "expired"]:
                    raise RuntimeError(f"Run ended with status: {run.status}")

                retry_count += 1
                time.sleep(1)

            if retry_count >= max_retries:
                raise RuntimeError("Run timed out after 30 seconds")

            # Get messages
            print("\nRetrieving assistant's response...")
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Return the last assistant message
            for message in messages.data:
                if message.role == "assistant":
                    print("Response retrieved successfully")
                    return message.content[0].text.value

            print("No assistant response found")
            return "No response generated."

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            raise RuntimeError(f"Failed to process PDF: {str(e)}")
