"""Download a local GGUF model during the AI service image build."""

import os
from pathlib import Path

from huggingface_hub import snapshot_download
from huggingface_hub.errors import GatedRepoError


def main() -> None:
    repo_id = os.environ.get(
        "LOCAL_MODEL_REPO_ID",
        "google/gemma-3-4b-it-qat-q4_0-gguf",
    )
    include = os.environ.get("LOCAL_MODEL_INCLUDE", "*.gguf")
    local_dir = Path(os.environ.get("LOCAL_MODEL_DIR", "/models/local-llm"))
    token = os.environ.get("HF_TOKEN") or None

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
            f"Request and accept access for {repo_id}, then rebuild ai-service. "
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
