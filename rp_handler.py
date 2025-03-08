import os
import sys
import urllib.parse
import runpod
import torch
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.abspath("src"))

import main as m

# Initialize GPU info if available
device = "cuda:0" if torch.cuda.is_available() else "cpu"
if device != "cpu":
    print(f"Using GPU: {torch.cuda.get_device_name()}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

def download_input_audio(url):
    """Download input audio from URL to a temporary file"""
    import tempfile
    import requests
    
    # Create a temporary file with the correct extension
    extension = os.path.splitext(url.split("?")[0])[1] or ".wav"
    temp_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    temp_file.close()
    
    # Download the file
    response = requests.get(url, stream=True)
    with open(temp_file.name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return temp_file.name

def handler(event):
    """
    RunPod handler function for voice conversion
    """
    try:
        # Get input parameters
        input_params = event.get("input", {})
        
        # Get input audio - can be a URL or base64 encoded data
        input_audio_url = input_params.get("input_audio")
        if not input_audio_url:
            return {"error": "No input audio provided"}
        
        # Download input audio if it's a URL
        if input_audio_url.startswith(("http://", "https://")):
            input_audio_path = download_input_audio(input_audio_url)
        else:
            return {"error": "Input audio must be a URL"}
        
        # Get RVC model
        rvc_model = input_params.get("rvc_model", "Obama")
        
        # Check for custom model URL
        custom_rvc_model_download_url = input_params.get("custom_rvc_model_download_url")
        if custom_rvc_model_download_url:
            custom_rvc_model_download_name = urllib.parse.unquote(
                custom_rvc_model_download_url.split("/")[-1]
            )
            custom_rvc_model_download_name = os.path.splitext(
                custom_rvc_model_download_name
            )[0]
            print(
                f"[!] The model will be downloaded as '{custom_rvc_model_download_name}'."
            )
            m.download_online_model(
                url=custom_rvc_model_download_url,
                dir_name=custom_rvc_model_download_name,
                overwrite=True
            )
            rvc_model = custom_rvc_model_download_name
        
        # Validate RVC model exists
        rvc_dirname = rvc_model
        if not os.path.exists(os.path.join(m.rvc_models_dir, rvc_dirname)):
            return {"error": f"The folder {os.path.join(m.rvc_models_dir, rvc_dirname)} does not exist."}
        
        # Get other parameters with defaults
        pitch_change = float(input_params.get("pitch_change", 0))
        f0_method = input_params.get("f0_method", "rmvpe")
        index_rate = float(input_params.get("index_rate", 0.5))
        filter_radius = int(input_params.get("filter_radius", 3))
        rms_mix_rate = float(input_params.get("rms_mix_rate", 0.25))
        protect = float(input_params.get("protect", 0.33))
        
        # Perform voice conversion
        output_path = m.voice_conversion(
            input_audio_path,
            rvc_dirname,
            pitch_change,
            f0_method,
            index_rate,
            filter_radius,
            rms_mix_rate,
            protect
        )
        print(f"[+] Converted audio generated at {output_path}")
        
        # Convert output to base64 or return URL
        output_format = input_params.get("output_format", "mp3")
        
        # If output is wav but mp3 is requested, convert to mp3
        final_output_path = output_path
        if output_format == "mp3" and output_path.endswith(".wav"):
            try:
                from pydub import AudioSegment
                mp3_path = output_path.replace(".wav", ".mp3")
                AudioSegment.from_wav(output_path).export(mp3_path, format="mp3")
                final_output_path = mp3_path
            except Exception as e:
                print(f"Warning: Failed to convert to MP3: {str(e)}")
        
        # Return the output file as base64
        import base64
        with open(final_output_path, "rb") as f:
            encoded_audio = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up temporary files
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
        
        return {
            "output": {
                "audio_base64": encoded_audio,
                "format": os.path.splitext(final_output_path)[1][1:],
                "message": "Voice conversion completed successfully"
            }
        }
        
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error: {error_message}")
        print(error_traceback)
        return {"error": error_message, "traceback": error_traceback}

# Start the RunPod serverless function
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
