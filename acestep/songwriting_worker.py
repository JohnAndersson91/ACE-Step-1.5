"""Draft English song lyrics with the existing local language model, then release RAM."""
import json
from pathlib import Path
import sys


def main():
    """Read a bounded request and write an editable draft; never download a model."""
    import torch
    from acestep.llm_inference import LLMHandler
    from transformers import AutoModelForCausalLM

    class DraftHandler(LLMHandler):
        """Load directly in the target precision to avoid a large temporary model copy."""
        def _load_pytorch_model(self,model_path,device):
            self.llm = AutoModelForCausalLM.from_pretrained(model_path,torch_dtype=self.dtype,
                low_cpu_mem_usage=True,local_files_only=True).to(device).eval()
            self.llm_backend,self.llm_initialized = "pt",True
            return True,"Local lyric model loaded"

    request_path,output = map(Path,sys.argv[1:3])
    request = json.loads(request_path.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    model = root/"checkpoints/acestep-5Hz-lm-1.7B"
    if not (model/"model.safetensors").is_file():
        raise RuntimeError("The existing lyric model is missing. No download was attempted.")
    torch.set_num_threads(4)
    device = "cuda" if torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>4.5*1024**3 else "cpu"
    handler = DraftHandler()
    status,ok = handler.initialize(str(root/"checkpoints"),str(model),backend="pt",
        device=device,dtype=torch.bfloat16 if device=="cuda" else torch.float32,offload_to_cpu=False)
    if not ok:
        raise RuntimeError("Could not start the installed lyric model: "+status)
    if device=="cpu":
        handler.llm = torch.ao.quantization.quantize_dynamic(
            handler.llm,{torch.nn.Linear},dtype=torch.qint8,inplace=True)
    handler.max_model_len = min(handler.max_model_len,2048)
    query = (f"{request['idea']}\nMusic: {request['style']}\n"
        f"Write an original English song for approximately {request['duration']} seconds. "
        "Use [Verse 1], [Chorus], [Verse 2], [Chorus], [Bridge], [Final Chorus] headings. "
        "Repeat the chorus hook. Write short singable lines. Mostly clean female singing; "
        "only two short screamed accents in the bridge or final chorus. No creature sounds. "
        "Do not name existing artists, songs, anime or characters.")
    metadata,status = handler.create_sample_from_query(query,instrumental=False,
        vocal_language="en",temperature=0.8,repetition_penalty=1.1)
    lyrics = metadata.get("lyrics","").strip()
    if not lyrics:
        raise RuntimeError("The local writer returned no lyrics.")
    output.write_text(json.dumps({"lyrics":lyrics},ensure_ascii=False),encoding="utf-8")


if __name__ == "__main__":
    main()
