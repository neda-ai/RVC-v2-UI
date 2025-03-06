import os
import urllib.request
import zipfile
import torch
from rvc import rvc_infer, load_hubert, get_vc, Config
import urllib.parse
import urllib.request
import gradio as gr
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rvc_models_dir = os.path.join(BASE_DIR, 'rvc_models')
output_dir = os.path.join(BASE_DIR, 'voice_output')

device = "cuda" if torch.cuda.is_available() else "cpu"
is_half = False if device == "cpu" else True

# Add this for debugging
if device != "cpu":
    print(f"Using GPU: {torch.cuda.get_device_name()}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

print(f"Using device: {device}")

def get_current_models(models_dir):
    models_list = os.listdir(models_dir)
    items_to_remove = ['hubert_base.pt', 'MODELS.txt', 'public_models.json', 'rmvpe.pt']
    return [item for item in models_list if item not in items_to_remove]

def update_models_list():
    models_l = get_current_models(rvc_models_dir)
    return gr.Dropdown(choices=models_l, value=models_l[0] if models_l else None)

def extract_zip(extraction_folder, zip_name):
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(extraction_folder)
    os.remove(zip_name)

def download_online_model(url, dir_name, progress=gr.Progress()):
    try:
        # Parse the URL and extract the filename
        parsed_url = urllib.parse.urlparse(url)
        zip_name = os.path.basename(parsed_url.path)
        
        # Remove any query parameters from the filename
        zip_name = zip_name.split('?')[0]
        
        extraction_folder = os.path.join(rvc_models_dir, dir_name)
        if os.path.exists(extraction_folder):
            raise gr.Error(f'Voice model directory {dir_name} already exists!')

        # Custom opener to report download progress
        class DownloadProgressBar():
            def __init__(self):
                self.pbar = None

            def __call__(self, block_num, block_size, total_size):
                if not self.pbar:
                    self.pbar = 0
                downloaded = block_num * block_size
                if downloaded < total_size:
                    progress(downloaded / total_size, desc="Downloading...")
                else:
                    progress(1.0, desc="Download complete")

        # Download the file with progress bar
        urllib.request.urlretrieve(url, zip_name, DownloadProgressBar())
        
        progress(0, desc="Extracting...")
        extract_zip(extraction_folder, zip_name)
        progress(1.0, desc="Extraction complete")
        
        return f'[+] {dir_name} Model successfully downloaded and extracted!'
    except Exception as e:
        raise gr.Error(str(e))
        
def upload_local_model(zip_file, dir_name, progress=gr.Progress()):
    try:
        extraction_folder = os.path.join(rvc_models_dir, dir_name)
        if os.path.exists(extraction_folder):
            raise gr.Error(f'Voice model directory {dir_name} already exists!')
        
        extract_zip(extraction_folder, zip_file.name)
        return f'[+] {dir_name} Model successfully uploaded!'
    except Exception as e:
        return f"Error: {str(e)}"

def load_rvc_model(rvc_model):
    model_dir = os.path.join(rvc_models_dir, rvc_model)
    model_path = os.path.join(model_dir, "model.pth")
    if not os.path.exists(model_path):
        pth_files = [f for f in os.listdir(model_dir) if f.endswith('.pth')]
        if pth_files:
            model_path = os.path.join(model_dir, pth_files[0])
        else:
            raise FileNotFoundError(f"No .pth file found in RVC model directory: {model_dir}")

    config = Config(device, is_half)
    return get_vc(device, is_half, config, model_path)

def voice_conversion(input_audio, rvc_model, pitch, f0_method, index_rate, filter_radius, rms_mix_rate, protect):
    try:
        hubert_model = load_hubert(device, is_half, os.path.join(rvc_models_dir, "hubert_base.pt"))
        cpt, version, net_g, tgt_sr, vc = load_rvc_model(rvc_model)

        output_filename = os.path.join(output_dir, f"converted_{os.path.basename(input_audio)}")
        output_filename = os.path.splitext(output_filename)[0] + '.wav'
        os.makedirs(output_dir, exist_ok=True)

        rvc_infer("", index_rate, input_audio, output_filename, pitch, f0_method, cpt, version, net_g, 
                  filter_radius, tgt_sr, rms_mix_rate, protect, 160, vc, hubert_model)

        return output_filename
    except Exception as e:
        raise gr.Error(f"Voice conversion failed: {str(e)}")

if __name__ == '__main__':
    voice_models = get_current_models(rvc_models_dir)

    with gr.Blocks(title='RVC Voice Changer') as app:
        with gr.Tab("Convert Voice"):
            with gr.Row():
                with gr.Column():
                    input_audio = gr.Audio(label='Input Audio', type='filepath')
                    rvc_model = gr.Dropdown(voice_models, label='Voice Models')
                    gr.Markdown("Select the AI voice model you want to use for conversion. Models are stored in the 'rvc_models' folder.")
                    ref_btn = gr.Button('Refresh Models 🔁', variant='primary')

                with gr.Column():
                    pitch = gr.Slider(-22, 22, value=0, step=1, label='Pitch Change')
                    gr.Markdown("Adjust the pitch of the output voice. Higher values make the voice higher, lower values make it deeper.")
                    
                    f0_method = gr.Dropdown(['rmvpe', 'mangio-crepe'], value='rmvpe', label='Pitch detection algorithm')
                    gr.Markdown("Choose the algorithm for pitch detection. RMVPE is generally good for clarity, while Mangio-Crepe can produce smoother vocals.")
                    
                    index_rate = gr.Slider(0, 1, value=0.5, label='Index Rate')
                    gr.Markdown("Controls how much of the AI voice's characteristics to keep. Higher values result in output closer to the AI voice.")
                    
                    filter_radius = gr.Slider(0, 7, value=3, step=1, label='Filter radius')
                    gr.Markdown("Applies median filtering to pitch results. Can help reduce breathiness. Higher values smooth out the pitch more.")
                    
                    rms_mix_rate = gr.Slider(0, 1, value=0.25, label='RMS mix rate')
                    gr.Markdown("Controls how much to mimic the original vocal's volume envelope. Higher values preserve more of the original dynamics.")
                    
                    protect = gr.Slider(0, 0.5, value=0.33, label='Protect rate')
                    gr.Markdown("Protects voiceless consonants and breath sounds from being converted. Set to 0.5 to disable protection.")

            with gr.Row():
                clear_btn = gr.Button("Clear")
                convert_btn = gr.Button("Convert", variant='primary')
                output_audio = gr.Audio(label='Converted Audio', type='filepath')

            ref_btn.click(update_models_list, None, outputs=rvc_model)
            convert_btn.click(voice_conversion,
                inputs=[input_audio, rvc_model, pitch, f0_method, index_rate, filter_radius, rms_mix_rate, protect],
                outputs=[output_audio])
            clear_btn.click(
                lambda: [None, None, 0, 'rmvpe', 0.5, 3, 0.25, 0.33],
                outputs=[input_audio, output_audio, pitch, f0_method, index_rate, filter_radius, rms_mix_rate, protect]
            )

        with gr.Tab('Download model'):
            model_zip_link = gr.Text(label='Download link to model')
            gr.Markdown("Provide a direct download link to a zip file containing the voice model. The zip should include a .pth model file and an optional .index file.")
            
            model_name = gr.Text(label='Name your model')
            gr.Markdown("Give your new model a unique name. This will be used as the folder name for the model files.")
            
            download_btn = gr.Button('Download 🌐', variant='primary')
            dl_output_message = gr.Text(label='Output Message', interactive=False)
            download_btn.click(download_online_model, inputs=[model_zip_link, model_name], outputs=dl_output_message)

        with gr.Tab('Upload model'):
            upload_zip = gr.File(label='Upload zip file', file_types=['.zip'])
            gr.Markdown("Upload a zip file containing your voice model. The zip should include a .pth model file and an optional .index file.")
            
            upload_model_name = gr.Text(label='Model name')
            gr.Markdown("Give your uploaded model a unique name. This will be used as the folder name for the model files.")
            
            upload_btn = gr.Button('Upload model', variant='primary')
            upload_output_message = gr.Text(label='Output Message', interactive=False)
            upload_btn.click(upload_local_model, inputs=[upload_zip, upload_model_name], outputs=upload_output_message)

    app.launch(server_name="0.0.0.0")
