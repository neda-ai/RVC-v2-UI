# RVC Voice Changer

[![Replicate](https://replicate.com/pseudoram/rvc-v2)](https://replicate.com/pseudoram/rvc-v2)

An autonomous pipeline to change voices using any RVC v2 trained AI voice model. This tool can be used to apply voice conversion to any audio input.

![](images/webui_generate.png?raw=true)

WebUI is under constant development and testing, but you can try it out right now on local!

## Update RVC Voice Changer to latest version

Install and pull any new requirements and changes by opening a command line window in the `RVC-v2-UI` directory and running the following commands.



```
pip install -r requirements.txt
git pull
```

For colab users, simply click `Runtime` in the top navigation bar of the colab notebook and `Disconnect and delete runtime` in the dropdown menu. 
Then follow the instructions in the notebook to run the webui.

## Colab notebook

(Hopefully coming soon)

## Setup

### Install Git and Python


Follow the instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) to install Git on your computer. Also follow this [guide](https://realpython.com/installing-python/) to install Python **VERSION 3.9** if you haven't already. Using other versions of Python may result in dependency conflicts.

Alternatively, you can use pyenv to manage Python versions:

1. Install pyenv following the instructions [here](https://github.com/pyenv/pyenv#installation).
2. Install Python 3.9:
```
pyenv install 3.9
```
3. Set it as your local Python version:
```
pyenv local 3.9
```


### Install ffmpeg

Follow the instructions [here](https://www.hostinger.com/tutorials/how-to-install-ffmpeg) to install ffmpeg on your computer.


### Clone RVC-v2-UI repository and set up virtual environment

Open a command line window and run these commands to clone this entire repository, create a virtual environment, and install the additional dependencies required.

```
git clone https://github.com/PseudoRAM/RVC-v2-UI
cd RVC-v2-UI
```
#### Create and activate virtual environment
##### Using pyenv
```
pyenv exec python -m venv venv
```
##### Not using pyenv
```
python -m venv venv
```

##### Activate virtual environment
##### Windows
```
venv\Scripts\activate
```
##### macOS and Linux
```
source venv/bin/activate
```

#### Install dependencies
```
pip install -r requirements.txt
```

### Download required models

Run the following command to download the required hubert base model.

```
python src/download_models.py
```


## Usage with WebUI

To run the RVC Voice Changer WebUI, run the following command.

```
python src/webui.py
```

| Flag                                       | Description |
|--------------------------------------------|-------------|
| `-h`, `--help`                             | Show this help message and exit. |
| `--share`                                  | Create a public URL. This is useful for running the web UI on Google Colab. |
| `--listen`                                 | Make the web UI reachable from your local network. |
| `--listen-host LISTEN_HOST`                | The hostname that the server will use. |
| `--listen-port LISTEN_PORT`                | The listening port that the server will use. |

Once the following output message `Running on local URL:  http://127.0.0.1:7860` appears, you can click on the link to open a tab with the WebUI.

### Download RVC models via WebUI

![](images/webui_dl_model.png?raw=true)

Navigate to the `Download model` tab, and paste the download link to the RVC model and give it a unique name.
You may search the [AI Hub Discord](https://discord.gg/aihub) where already trained voice models are available for download. You may refer to the examples for how the download link should look like.
The downloaded zip file should contain the .pth model file and an optional .index file.

Once the 2 input fields are filled in, simply click `Download`! Once the output message says `[NAME] Model successfully downloaded!`, you should be able to use it in the `Convert Voice` tab after clicking the refresh models button!

### Upload RVC models via WebUI

![](images/webui_upload_model.png?raw=true)

For people who have trained RVC v2 models locally and would like to use them for voice conversion.
Navigate to the `Upload model` tab, and follow the instructions.
Once the output message says `[NAME] Model successfully uploaded!`, you should be able to use it in the `Convert Voice` tab after clicking the refresh models button!

### Running the pipeline via WebUI

![](images/webui_generate.png?raw=true)

- From the Voice Models dropdown menu, select the voice model to use. Click `Refresh Models` if you added the files manually to the [rvc_models](rvc_models) directory to refresh the list.
- In the Input Audio field, upload your audio file.
- Adjust the pitch as needed. This changes the pitch of the output voice.
- Other advanced options for Voice conversion can be viewed by clicking the accordion arrow to expand.

Once all options are filled in, click `Convert` and the AI generated voice should appear in a few moments depending on your GPU.

## Usage with CLI

### Running the pipeline

To run the voice conversion pipeline using the command line, run the following command:

```
python src/main.py <input_audio> <rvc_model> [pitch] [f0_method] [index_rate] [filter_radius] [rms_mix_rate] [protect]
```

| Parameter                  | Description |
|----------------------------|-------------|
| `input_audio`              | Path to the input audio file. |
| `rvc_model`                | Name of the RVC model to use. |
| `pitch`                    | (Optional) Pitch change in semitones. Default is 0. |
| `f0_method`                | (Optional) Pitch detection algorithm. Options: 'rmvpe' (default) or 'mangio-crepe'. |
| `index_rate`               | (Optional) Index rate for the voice conversion. Default is 0.5. Range: 0 to 1. |
| `filter_radius`            | (Optional) Filter radius for median filtering. Default is 3. Range: 0 to 7. |
| `rms_mix_rate`             | (Optional) RMS mix rate. Default is 0.25. Range: 0 to 1. |
| `protect`                  | (Optional) Protect rate to preserve some original voice characteristics. Default is 0.33. Range: 0 to 0.5. |

Example usage:
```
python src/main.py "path/to/input/audio.wav" "JohnDoe" 2 rmvpe 0.7 3 0.3 0.35
```
This command will convert the voice in "audio.wav" using the "JohnDoe" RVC model, raising the pitch by 2 semitones, using the 'rmvpe' pitch detection algorithm, with an index rate of 0.7, filter radius of 3, RMS mix rate of 0.3, and protect rate of 0.35.


## Manual Download of RVC models

Unzip (if needed) and transfer the `.pth` and `.index` files to a new folder in the [rvc_models](rvc_models) directory. Each folder should only contain one `.pth` and one `.index` file.

The directory structure should look something like this:
```
├── rvc_models
│   ├── John
│   │   ├── JohnV2.pth
│   │   └── added_IVF2237_Flat_nprobe_1_v2.index
│   ├── May
│   │   ├── May.pth
│   │   └── added_IVF2237_Flat_nprobe_1_v2.index
│   ├── MODELS.txt
│   └── hubert_base.pt
├── voice_output
└── src
 ```



## Terms of Use

The use of the converted voice for the following purposes is prohibited.

* Criticizing or attacking individuals.
* Advocating for or opposing specific political positions, religions, or ideologies.
* Publicly displaying strongly stimulating expressions without proper zoning.
* Selling of voice models and generated voice clips.
* Impersonation of the original owner of the voice with malicious intentions to harm/hurt others.
* Fraudulent purposes that lead to identity theft or fraudulent phone calls.

## Disclaimer

I am not liable for any direct, indirect, consequential, incidental, or special damages arising out of or in any way connected with the use/misuse or inability to use this software.