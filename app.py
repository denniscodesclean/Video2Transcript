import os
import subprocess
import whisper
from youtube_transcript_api import YouTubeTranscriptApi
import transformers
from flask import Flask, render_template, request

# Suppress warnings from transformers
transformers.logging.set_verbosity_error()

# Suppress all warnings globally
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__,template_folder="templates/app")

class VideoToTranscript:
    def __init__(self, video_url):
        self.video_url = video_url
        self.video_id = video_url.split("watch?v=")[-1]

    def clear_previous_files(self):
        output_audio_file = "output_audio.mp3"
        if os.path.exists(output_audio_file):
            os.remove(output_audio_file)
            print(f"Cleared previous file: {output_audio_file}")

    def get_transcript(self):
        self.clear_previous_files()  # Clear previous files before starting the task
        try:
            # Fetch the transcript from YouTube
            transcript = YouTubeTranscriptApi.get_transcript(self.video_id)

            # Combine text from transcript
            transcript_text = "\n".join([item['text'] for item in transcript])

            print("Transcript fetched successfully from YouTube API:")
            print(transcript_text)
            return transcript_text
        except Exception as e:
            # Log the exception error for debugging
            print(f"Failed to fetch transcript from YouTube API: {e}")
            print("Falling back to Whisper transcription...")
            return self.download_and_transcribe()

    def download_and_transcribe(self):
        # Define the output file name for the audio
        output_audio_file = "./output_audio.mp3"

        # Command to download audio and save it as MP3
        command = [
            "yt-dlp",
            "-f", "bestaudio",         # Best audio format
            "--extract-audio",         # Extract audio only
            "--audio-format", "mp3",   # Convert to MP3
            "-o", output_audio_file,   # Output file path
            self.video_url
        ]

        # Run the command to download audio
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the MP3 file exists
            if os.path.exists(output_audio_file):
                print(f"Audio downloaded successfully as MP3: {output_audio_file}")

                # Load Whisper model
                model = whisper.load_model("base")

                # Transcribe the audio
                result = model.transcribe(output_audio_file)

                print("Transcription completed using Whisper:")
                print(result["text"])
                return result["text"]
            else:
                print("Audio file not found after download.")
                return "Audio download failed."
        except Exception as e:
            # Log the exception error for debugging
            print(f"Error during audio download or Whisper transcription: {e}")
            return f"Error: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        video_to_transcript = VideoToTranscript(video_url)
        transcript = video_to_transcript.get_transcript()

        if transcript:
            return render_template('index.html', transcript=transcript)
        else:
            # Return the error message in the template
            return render_template('index.html', error="Failed to generate transcript.")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
