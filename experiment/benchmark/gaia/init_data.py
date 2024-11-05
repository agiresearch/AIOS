import os

from huggingface_hub import snapshot_download

DOWNLOAD_PATH = os.path.dirname(os.path.realpath(__file__))
REPO_PATH = os.path.join(DOWNLOAD_PATH, "gaia")


def download_gaia():
    """Download the GAIA benchmark from Hugging Face."""

    if not os.path.isdir(DOWNLOAD_PATH):
        os.mkdir(DOWNLOAD_PATH)

    """Download the GAIA dataset from Hugging Face Hub"""
    snapshot_download(
        repo_id="gaia-benchmark/GAIA",
        repo_type="dataset",
        local_dir_use_symlinks=True,
        local_dir=REPO_PATH,
    )


if __name__ == "__main__":
    download_gaia()
