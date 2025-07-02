import os
from openai import OpenAI
from pathlib import Path
import html2text

from chapter_sync.formats.iformat import IFormat

class OpenAiAudioFormat(IFormat):
    """
    A class representing the OpenAi Audio format for exporting data.
    It implements the IFormat interface.
    """

    def __init__(self):
        """
        Initializes the KokoroFormat instance.
        The first letter of the voice parameter is used as the language code.
        """

        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.voice = os.getenv("OPENAI_VOICE", "en-US-Wavenet-D")

        self.client = OpenAI(base_url = self.base_url, api_key = self.api_key)

        # Use the first letter of the voice name as the language code
        
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0
        self.h2t.single_line_break = True


    def export(self, text, location, filename):
        """
        Generates and exports the Kokoro format to the specified filesystem location.
        """

        print("Exporting Kokoro format...")

        # Ensure the output directory exists
        if not os.path.exists(location):
            os.makedirs(location)
            print(f"Created directory: {location}")

        filename = filename + ".mp3"
        # Construct the full output file path
        output_path = os.path.join(location, filename)

        print("Converting html to text")
        stripped_text = self.h2t.handle(text)

        print("Create Audio chunk array")
        audio_chunks = []


        with self.client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            input=stripped_text,
          ) as response:
              response.stream_to_file(output_path)
