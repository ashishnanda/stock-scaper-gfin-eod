import os
import requests
import zipfile
import csv
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment

token = os.getenv("GITHUB_TOKEN")

# --- USER CONFIG ---

REPO = "ashishnanda/stock-scaper-gfin-eod"
ARTIFACT_NAME = "daily-stock-prices"
TOKEN = os.getenv("GITHUB_TOKEN")
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_PATH, "successful_downloads.csv")
DOWNLOAD_DIR = os.path.join(BASE_PATH, "downloaded_data")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Step 1: Load run_ids of already downloaded artifacts ---
downloaded_ids = set()
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            downloaded_ids.add(row['run_id'])

# --- Step 2: Get recent workflow runs ---
runs_url = f"https://api.github.com/repos/{REPO}/actions/runs"
runs_resp = requests.get(runs_url, headers=headers)
runs_resp.raise_for_status()
runs = runs_resp.json()["workflow_runs"]

# --- Step 3: Prepare log writer ---
file_exists = os.path.exists(LOG_FILE)
log_file = open(LOG_FILE, "a", newline='')
log_writer = csv.DictWriter(log_file, fieldnames=["run_id", "run_date", "filename_saved", "status", "download_timestamp"])
if not file_exists:
    log_writer.writeheader()

# --- Step 4: Process eligible runs ---
for run in runs:
    run_id = str(run["id"])
    run_date_obj = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    run_date = run_date_obj.date().isoformat()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Skip already downloaded
    if run_id in downloaded_ids:
        continue

    # Filter: only successful runs
    if run["conclusion"] != "success": 
        continue

    try:
        # Step 5: Get artifact list
        artifacts_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts"
        artifacts_resp = requests.get(artifacts_url, headers=headers)
        artifacts_resp.raise_for_status()
        artifacts = artifacts_resp.json()["artifacts"]
        artifact = next((a for a in artifacts if a["name"] == ARTIFACT_NAME), None)

        if not artifact:
            log_writer.writerow({
                "run_id": run_id,
                "run_date": run_date,
                "filename_saved": "",
                "status": "artifact_not_found",
                "download_timestamp": timestamp
            })
            continue

        # Step 6: Download ZIP
        zip_url = artifact["archive_download_url"]
        zip_path = os.path.join(BASE_PATH, f"{ARTIFACT_NAME}_{run_id}.zip")

        try:
            with requests.get(zip_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            log_writer.writerow({
                "run_id": run_id,
                "run_date": run_date,
                "filename_saved": "",
                "status": "download_failed",
                "download_timestamp": timestamp
            })
            continue

        # Step 7: Extract ZIP
        try:
            month_folder = run_date_obj.strftime("%Y-%m")
            output_folder = os.path.join(DOWNLOAD_DIR, month_folder)
            os.makedirs(output_folder, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    out_file = os.path.join(output_folder, f"{run_date}.csv")
                    zip_ref.extract(name, output_folder)
                    os.rename(os.path.join(output_folder, name), out_file)

            os.remove(zip_path)

            log_writer.writerow({
                "run_id": run_id,
                "run_date": run_date,
                "filename_saved": out_file,
                "status": "success",
                "download_timestamp": timestamp
            })

        except Exception as e:
            log_writer.writerow({
                "run_id": run_id,
                "run_date": run_date,
                "filename_saved": zip_path,
                "status": "extraction_failed",
                "download_timestamp": timestamp
            })
            continue

    except Exception as e:
        print(f"❌ Unexpected error with run {run_id}: {e}")
        # Optional: log unknown failure type

log_file.close()

# --- Step 8: Print summary report ---
from collections import Counter

with open(LOG_FILE, newline='') as f:
    reader = csv.DictReader(f)
    statuses = [row["status"] for row in reader if row["download_timestamp"] == timestamp]

status_counts = Counter(statuses)

print("\n✅ Summary:")
for status, count in status_counts.items():
    print(f"- {status}: {count}")

print("✅ Script complete.")
