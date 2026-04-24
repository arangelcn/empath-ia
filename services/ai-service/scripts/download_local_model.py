"""Download a local GGUF model for the AI service runtime."""

import os
from pathlib import Path

from huggingface_hub.errors import GatedRepoError
from huggingface_hub import snapshot_download


DEFAULT_REPO_ID = "ggml-org/gemma-4-E4B-it-GGUF"
DEFAULT_INCLUDE = "gemma-4-E4B-it-Q4_K_M.gguf"


def get_hf_token() -> str | None:
    """Return the first configured Hugging Face token alias."""
    return (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_TOKEN")
        or os.environ.get("HUGGIN_FACE_TOKEN")
        or None
    )


def main() -> None:
    repo_id = os.environ.get(
        "LOCAL_MODEL_REPO_ID", DEFAULT_REPO_ID
    )
    include = os.environ.get("LOCAL_MODEL_INCLUDE", DEFAULT_INCLUDE)
    local_dir = Path(os.environ.get("LOCAL_MODEL_DIR", "/models/local-llm"))
    token = get_hf_token()

    local_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading local model repo: {repo_id}")
    print(f"Include pattern: {include}")
    print(f"Target directory: {local_dir}")
    print(f"HF token configured: {'yes' if token else 'no'}")

    try:
        snapshot_download(
            repo_id=repo_id,
            allow_patterns=[include],
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            token=token,
        )
    except GatedRepoError as exc:
        raise RuntimeError(
            "Cannot download the configured gated Hugging Face model. "
            f"Request and accept access for {repo_id}, then restart ai-service. "
            "You can also set LOCAL_MODEL_REPO_ID to an accessible GGUF repository."
        ) from exc

    gguf_files = sorted(local_dir.rglob("*.gguf"))
    if not gguf_files:
        raise RuntimeError(f"No GGUF files found after download in {local_dir}")

    print("Downloaded GGUF files:")
    for model_file in gguf_files:
        print(f"- {model_file}")


if __name__ == "__main__":
    main()
