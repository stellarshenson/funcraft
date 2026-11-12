"""Load Ming-3.0-tts-0.5B on the RTX PRO 4000 with FlashAttention 2 on its Qwen2 model.

Import this module before torch: it fixes the GPU and offline mode through environment variables.
"""
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["HF_HUB_OFFLINE"] = "1"

import sys
from pathlib import Path

import torch
from huggingface_hub import snapshot_download

LAUNCH_DIR = Path.cwd()  # the model code needs its own folder as working directory
ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "resources" / "models" / "Ming-3.0-tts"
MODEL = "inclusionAI/Ming-3.0-tts-0.5B"
REVISION = "7247f4c94a5b2e987404ed28a5cfec41b1a4ca61"

sys.path.insert(0, str(CODE))
os.chdir(CODE)
import configuration_bailingmm  # noqa: E402
from ming_tts import MingTTS  # noqa: E402


def load_model(attention: str = "flash_attention_2") -> MingTTS:
    """Load the model once and print the device name.

    Args:
        attention: attention implementation of the Qwen2 model (`flash_attention_2` or `sdpa`).

    Returns:
        The loaded `MingTTS` on GPU 0.
    """
    original_init = configuration_bailingmm.BailingMMConfig.__init__

    def init_with_attention(self, llm_config=None, *args, **kwargs):
        if isinstance(llm_config, dict):
            llm_config["_attn_implementation"] = attention
        original_init(self, llm_config, *args, **kwargs)

    configuration_bailingmm.BailingMMConfig.__init__ = init_with_attention
    print("device:", torch.cuda.get_device_name(0))
    model = MingTTS(snapshot_download(MODEL, revision=REVISION), text_normalization=False)
    print("llm attention:", model.model.model.config._attn_implementation)
    return model
