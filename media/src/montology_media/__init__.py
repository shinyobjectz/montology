"""montology-media: encode and convert, the invoked-never-linked way.

Images run in-process (Pillow — already a wheel everywhere). Audio and
video run through an INVOKED ffmpeg — same doctrine as whisper.cpp and
Ollama: a binary the user installs once, a repair message when absent,
never a compile. `to_wav16` is the bridge that feeds any mp3/m4a/mp4 into
the zoo's transcribe lane; `data_uri` inlines assets for self-contained
emails and artifacts.
"""

from .av import extract_gif, thumbnail, to_wav16, transcode, trim
from .images import convert_image, resize_image
from .inline import data_uri

__all__ = ["convert_image", "data_uri", "extract_gif", "resize_image",
           "thumbnail", "to_wav16", "transcode", "trim"]
