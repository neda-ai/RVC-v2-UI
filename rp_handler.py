import logging
import os
import sys
import tempfile
import urllib.parse
from pathlib import Path

import httpx
import runpod
import ufiles

from src import config, main, schemas

config.Settings.config_logger()
sys.path.insert(0, str((config.Settings / "src").resolve()))


def download_input_audio(url):
    """Download input audio from URL to a temporary file"""

    # Create a temporary file with the correct extension
    url_parsed = urllib.parse.urlparse(url)
    url_path = Path(url_parsed.path)
    extension = url_path.suffix or ".wav"
    temp_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    temp_file.close()

    # Download the file
    with httpx.stream("GET", url) as response:
        response.raise_for_status()  # Raise an error if the request failed
        with open(temp_file.name, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

    return temp_file.name


def convert_to_mp3(path: Path) -> Path:
    try:
        from pydub import AudioSegment

        mp3_path = path.replace(".wav", ".mp3")
        AudioSegment.from_wav(path).export(mp3_path, format="mp3")
        return mp3_path
    except Exception as e:
        logging.error(f"Error converting to MP3: {str(e)}")
        return None


def encode_audio(path: Path) -> str:
    import base64

    with open(path, "rb") as f:
        encoded_audio = base64.b64encode(f.read()).decode("utf-8")
    return encoded_audio


def handler(event):
    """
    RunPod handler function for voice conversion
    """
    try:
        # Get input parameters
        input_params: dict[str, str] = event.get("input", {})
        input_data = schemas.RVCV2InputSchema(**input_params)
        input_audio_path = download_input_audio(input_data.input_audio)

        if input_data.custom_rvc_model_download_url:
            logging.info(
                f"[+] Downloading RVC model from {input_data.custom_rvc_model_download_url}"
            )
            main.download_online_model(
                url=input_data.custom_rvc_model_download_url,
                dir_name=input_data.rvc_model_name,
            )

        # Validate RVC model exists
        if not input_data.check_rvc_model_exists():
            return {"error": f"The folder {input_data.rvc_model_path} does not exist."}

        # Perform voice conversion
        output_path = main.voice_conversion(
            input_audio=input_audio_path,
            rvc_model=input_data.rvc_model_name,
            pitch=input_data.pitch_change,
            f0_method=input_data.f0_method,
            index_rate=input_data.index_rate,
            filter_radius=input_data.filter_radius,
            rms_mix_rate=input_data.rms_mix_rate,
            protect=input_data.protect,
        )
        logging.info(f"[+] Converted audio generated at {output_path}")

        # If output is wav but mp3 is requested, convert to mp3
        final_output_path = output_path
        if input_data.output_format == "mp3" and output_path.endswith(".wav"):
            final_output_path = convert_to_mp3(output_path)

        ufiles_client = ufiles.UFiles(
            api_key=config.Settings.UFILES_API_KEY,
            ufiles_base_url=config.Settings.UFILES_BASE_URL,
        )
        uploaded = ufiles_client.upload_file(
            file_path=final_output_path,
            file_name=input_data.upload_filename,
        )
        output = {
            "output_url": uploaded.url,
            "format": input_data.output_format,
            "message": "Voice conversion completed successfully",
        }

        if input_data.webhook_url:
            response = httpx.post(input_data.webhook_url, json=output)
            # response.raise_for_status()
            logging.info(f"[+] Webhook sent {response.status_code}")
            logging.info(f"[+] Webhook response: {response.text}")

        # Clean up temporary files
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)

        return {"output": output}

    except Exception as e:
        import traceback

        error_message = str(e)
        error_traceback = traceback.format_exc()
        logging.error(f"Error: {error_message}")
        logging.error(error_traceback)
        return {"error": error_message, "traceback": error_traceback}


# Start the RunPod serverless function
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
