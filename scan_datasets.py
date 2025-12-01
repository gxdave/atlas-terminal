"""
Scan Data folder and generate metadata for hosted datasets
"""
import os
import json
from pathlib import Path
from datetime import datetime

# Path to datasets folder (now local in project)
DATA_ROOT = Path("data/datasets")

# Only include these timeframes
ALLOWED_TIMEFRAMES = ['D1', 'H1', 'M1']

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

def scan_datasets():
    """Scan all CSV files in Data folder"""
    datasets = []
    total_size = 0

    for csv_file in DATA_ROOT.rglob("*.csv"):
        relative_path = csv_file.relative_to(DATA_ROOT)
        size_mb = get_file_size_mb(csv_file)
        total_size += size_mb

        # Parse instrument and timeframe from path
        parts = str(relative_path).split(os.sep)
        instrument = parts[0] if len(parts) > 0 else "Unknown"
        filename = parts[-1]

        # Extract timeframe from filename
        timeframe = filename.replace(".csv", "").split("_")[-1]

        # Skip if not in allowed timeframes
        if timeframe not in ALLOWED_TIMEFRAMES:
            continue

        dataset_info = {
            "id": str(relative_path).replace("\\", "/").replace(".csv", ""),
            "instrument": instrument,
            "timeframe": timeframe,
            "filename": filename,
            "path": str(relative_path).replace("\\", "/"),
            "size_mb": round(size_mb, 2),
            "last_modified": datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat()
        }

        datasets.append(dataset_info)

    # Sort by instrument and timeframe
    datasets.sort(key=lambda x: (x['instrument'], x['timeframe']))

    # Create metadata
    metadata = {
        "total_datasets": len(datasets),
        "total_size_mb": round(total_size, 2),
        "last_updated": datetime.now().isoformat(),
        "instruments": list(set([d['instrument'] for d in datasets])),
        "timeframes": list(set([d['timeframe'] for d in datasets])),
        "datasets": datasets
    }

    return metadata

if __name__ == "__main__":
    print("Scanning datasets...")
    metadata = scan_datasets()

    print(f"\nFound {metadata['total_datasets']} datasets")
    print(f"Total size: {metadata['total_size_mb']:.2f} MB")
    print(f"Instruments: {', '.join(metadata['instruments'])}")
    print(f"Timeframes: {', '.join(sorted(metadata['timeframes']))}")

    # Save metadata
    output_path = "data/metadata.json"
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadata saved to {output_path}")
