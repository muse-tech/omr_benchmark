import os
import json
import shutil
from huggingface_hub import hf_hub_download

repo_id = "musegroup/omr_benchmark"

pdf_dir = "./data/pdf"
mscz_dir = "./data/mscz"
dataset_dir = "./data/omr_benchmark"
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(mscz_dir, exist_ok=True)
os.makedirs(dataset_dir, exist_ok=True)

samples = None
print("Downloading benchmark_dataset.json...")
try:
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename="benchmark_dataset.json",
        repo_type="dataset"
    )
    shutil.copy(downloaded_path, os.path.join(dataset_dir, "benchmark_dataset.json"))
    print(f"Dataset metadata saved to {dataset_dir}")

    with open(downloaded_path, 'r') as f:
        dataset_json = json.load(f)

    samples = []
    for col_key in sorted(dataset_json.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        sample_data = dataset_json[col_key]
        if isinstance(sample_data, dict) and "score" in sample_data and "pdf_image" in sample_data:
            samples.append({
                "id": col_key,
                "pdf_image": sample_data["pdf_image"],
                "score": sample_data["score"]
            })
    print(f"Found {len(samples)} samples in dataset")
except Exception as e:
    print(f"  Error: Could not download benchmark_dataset.json: {e}")
    exit(1)

files_to_download = samples
print(f"\nDownloading {len(files_to_download)} files...")

for i, sample in enumerate(files_to_download):
    sample_id = sample["id"]
    pdf_file_path = sample["pdf_image"]
    pdf_path = os.path.join(pdf_dir, f"score_file_{sample_id}.pdf")
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=pdf_file_path,
            repo_type="dataset"
        )
        with open(downloaded_path, "rb") as src:
            with open(pdf_path, "wb") as dst:
                dst.write(src.read())
    except Exception as e:
        print(f"  Warning: Could not download PDF for sample {sample_id}: {e}")

    score_file_path = sample["score"]
    mscz_path = os.path.join(mscz_dir, f"score_file_{sample_id}.mscz")
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=score_file_path,
            repo_type="dataset"
        )
        with open(downloaded_path, "rb") as src:
            with open(mscz_path, "wb") as dst:
                dst.write(src.read())
    except Exception as e:
        print(f"  Warning: Could not download MuseScore file for sample {sample_id}: {e}")
    
    if (i + 1) % 10 == 0:
        print(f"  Processed {i + 1}/{len(files_to_download)} files...")

print(f"\nDownload complete!")
print(f"  PDF files: {pdf_dir}")
print(f"  MuseScore files: {mscz_dir}")
