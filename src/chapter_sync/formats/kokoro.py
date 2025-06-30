from kokoro import KPipeline
import os
import soundfile as sf
import torch
import numpy as np
import html2text

from chapter_sync.formats.iformat import IFormat

class KokoroFormat(IFormat):
    """
    A class representing the Kokoro format for exporting data.
    It implements the IFormat interface.
    """

    def __init__(self, voice):
        """
        Initializes the KokoroFormat instance.
        The first letter of the voice parameter is used as the language code.
        """

        if not voice or not isinstance(voice, str):
            raise ValueError("The 'voice' parameter must be a non-empty string.")

        # Use the first letter of the voice name as the language code
        self.voice = voice
        self.lang_code = voice[0]

        print(f"Creating Pipeline with voice: '{voice}'")

        self.pipeline = KPipeline(lang_code=self.lang_code)
        
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0
        self.h2t.single_line_break = True

        print("KokoroFormat initialized")

    def export(self, text, location, filename):
        """
        Generates and exports the Kokoro format to the specified filesystem location.
        """

        print("Exporting Kokoro format...")

        # Ensure the output directory exists
        if not os.path.exists(location):
            os.makedirs(location)
            print(f"Created directory: {location}")

        filename = filename + ".wav"
        # Construct the full output file path
        output_path = os.path.join(location, filename)

        print("Converting html to text")
        stripped_text = self.h2t.handle(text)

        print("Create Audio chunk array")
        audio_chunks = []

        print("Generating content")
        generator = self.pipeline(stripped_text, voice=self.voice, speed=1, split_pattern=r'\n+')
    
        for i, (gs, ps, audio) in enumerate(generator):
            #print(f"Generated chunk {i}...")
            audio_chunks.append(audio)

        if not audio_chunks:
            print("TTS pipeline did not produce any audio.")
            return {"error": "TTS generation failed to produce audio."}

        full_audio = np.concatenate(audio_chunks)
        print("Audio chunks concatenated.")

        # wav_buffer = io.BytesIO()

        try:
            sf.write(output_path, full_audio, 24000, format='WAV', subtype='PCM_16')
            print(f"WAV file successfully saved to: {output_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
            return {"error": f"Failed to write audio to file: {e}"}

        # wav_buffer.seek(0)

        # return StreamingResponse(
        #     wav_buffer,
        #     media_type="audio/wav",
        #     headers={"Content-Disposition": f'attachment; filename="{chapter.filename()}.wav"'}
        # )