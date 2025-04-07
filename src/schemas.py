import urllib.parse
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator

from .config import Settings


class RVCV2InputSchema(BaseModel):
    input_audio: str
    custom_rvc_model_download_url: str | None = None
    rvc_model: str = "Obama"
    pitch_change: float = 0
    f0_method: str = "rmvpe"
    index_rate: float = 0.5
    filter_radius: int = 3
    rms_mix_rate: float = 0.25
    protect: float = 0.33
    webhook_url: str | None = None

    output_format: Literal["mp3", "wav"] = "wav"

    @field_validator("input_audio")
    def validate_input_audio(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("Input audio must be a URL")
        return v

    @property
    def input_audio_path(self) -> Path:
        return Path(self.input_audio)

    @property
    def rvc_model_name(self) -> Path:
        if self.custom_rvc_model_download_url:
            parsed = urllib.parse.urlparse(self.custom_rvc_model_download_url)
            rvc_path = Path(parsed.path)
            return rvc_path.stem
        return self.rvc_model

    @property
    def rvc_model_path(self) -> Path:
        return Settings.rvc_models_dir / self.rvc_model_name

    @property
    def output_path(self) -> Path:
        return Settings.output_dir / f"{self.rvc_model_name}.wav"

    @property
    def upload_filename(self) -> str:
        return f"neda/{self.rvc_model_name}.{self.output_format}"

    def check_rvc_model_exists(self) -> bool:
        return self.rvc_model_path.exists()
