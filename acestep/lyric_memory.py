"""Reuse the music handler's existing offload support while the lyric writer runs."""


def release_idle_music_gpu(handler):
    """Offload only CUDA handlers already configured for CPU offload; next generation reloads them."""
    if handler is None or not getattr(handler,"offload_to_cpu",False):
        return
    if str(getattr(handler,"device","")).split(":")[0]!="cuda":
        return
    for name in ("model","text_encoder","vae"):
        model = getattr(handler,name,None)
        if model is not None:
            handler._recursive_to_device(model,"cpu")
    handler._release_system_memory()
