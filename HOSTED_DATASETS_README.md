# 📊 Hosted Datasets Feature - Atlas Terminal V1.1.2

## Overview

Atlas Terminal now supports **hosted datasets** for the Probability Analyzer, eliminating the need for manual CSV uploads. Users can select from pre-loaded datasets and analyze them instantly.

---

## 🎯 Features

- ✅ **57 Pre-loaded Datasets** (240 MB total)
- ✅ **8 Instruments**: EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, XAUUSD, BTCUSD, US500
- ✅ **8 Timeframes**: M1, M5, M15, M30, H1, H4, D1
- ✅ **API Endpoints** for listing and loading datasets
- ✅ **No Manual Upload Required**

---

## 🔌 API Endpoints

### 1. List All Datasets
```http
GET /api/datasets
```

**Response:**
```json
{
  "total_datasets": 57,
  "total_size_mb": 240.08,
  "instruments": ["EURUSD", "GBPUSD", "XAUUSD", ...],
  "timeframes": ["M1", "M5", "H1", "H4", "D1", ...],
  "datasets": [
    {
      "id": "EURUSD/EURUSD_H1",
      "instrument": "EURUSD",
      "timeframe": "H1",
      "filename": "EURUSD_H1.csv",
      "size_mb": 5.72,
      "last_modified": "2025-10-28T20:37:02.461274"
    },
    ...
  ]
}
```

### 2. Get Specific Dataset Info
```http
GET /api/datasets/{dataset_id}
```

**Example:**
```http
GET /api/datasets/EURUSD/EURUSD_H1
```

**Response:**
```json
{
  "dataset_id": "EURUSD/EURUSD_H1",
  "rows": 100000,
  "columns": ["Time", "Open", "High", "Low", "Close", "Volume"],
  "size_mb": 5.72,
  "first_date": "2020-01-01 00:00:00",
  "last_date": "2025-10-28 23:00:00",
  "sample": [...]
}
```

### 3. Analyze Hosted Dataset
```http
POST /api/analyze/hosted
```

**Request Body:**
```json
{
  "dataset_id": "EURUSD/EURUSD_H1"
}
```

**Response:**
```json
{
  "dataset_id": "EURUSD/EURUSD_H1",
  "instrument": "EURUSD",
  "timeframe": "H1",
  "total_rows": 100000,
  "date_range": {
    "start": "2020-01-01",
    "end": "2025-10-28"
  },
  "analysis": {
    "status": "completed",
    "probability": "..."
  }
}
```

---

## 💻 Local Development Setup

### 1. Generate Metadata

Run this script to scan your Data folder and generate metadata:

```bash
cd "C:\Users\dgauc\OneDrive\Desktop\Coding\Atlas Terminal\V1.1.1"
python scan_datasets.py
```

This creates `data/metadata.json` with all dataset information.

### 2. Configure Data Path

The backend reads from the `DATA_ROOT` environment variable:

```python
# Default local path
DATA_ROOT = "C:/Users/dgauc/OneDrive/Desktop/Coding/Data"

# Or set via environment variable
export DATA_ROOT_PATH="/path/to/your/data"
```

### 3. Start Server

```bash
python -m uvicorn backend:app --reload
```

### 4. Test Endpoints

```bash
# List datasets
curl http://localhost:8000/api/datasets

# Get specific dataset
curl http://localhost:8000/api/datasets/EURUSD/EURUSD_H1

# Analyze dataset
curl -X POST http://localhost:8000/api/analyze/hosted \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "EURUSD/EURUSD_H1"}'
```

---

## 🚀 Railway Deployment

### Challenge: 240MB Data Size

Railway has a 500MB deployment size limit. Since the data is 240MB, we have **two options**:

### Option 1: Cloud Storage (Recommended for Production)

**Use Cloudflare R2 or AWS S3:**

1. Upload your Data folder to cloud storage
2. Set environment variable in Railway:
   ```
   DATA_ROOT_PATH=https://your-bucket.r2.cloudflarestorage.com/data
   ```
3. Modify backend to download CSV from URL instead of local filesystem

**Benefits:**
- ✅ Unlimited data size
- ✅ Fast CDN delivery
- ✅ Easy updates (just upload new files)

**Cost:**
- Cloudflare R2: Free for first 10GB
- AWS S3: ~$0.023/GB/month

### Option 2: Railway Volume (Simple but Limited)

**Use Railway's persistent volumes:**

1. Create a volume in Railway
2. Upload data to the volume
3. Mount volume to `/data` in your service

**Benefits:**
- ✅ Simple setup
- ✅ Direct filesystem access

**Limitations:**
- ⚠️ Manual upload required
- ⚠️ Harder to update

---

## 🔧 Integration with Probability Analyzer

### Current Status

The endpoints are ready, but need integration with your existing Probability Analyzer logic.

### Next Steps

1. **Update Frontend**: Add dropdown to select hosted datasets
2. **Integrate Analysis**: Connect `/api/analyze/hosted` with Prob_Analyzer logic
3. **Add Caching**: Cache frequently used datasets

### Example Frontend Integration

```javascript
// Fetch available datasets
const datasets = await fetch('/api/datasets').then(r => r.json());

// Display in dropdown
const select = document.getElementById('dataset-select');
datasets.datasets.forEach(ds => {
  const option = document.createElement('option');
  option.value = ds.id;
  option.text = `${ds.instrument} ${ds.timeframe} (${ds.size_mb}MB)`;
  select.appendChild(option);
});

// Analyze selected dataset
async function analyzeDataset() {
  const datasetId = select.value;
  const result = await fetch('/api/analyze/hosted', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId })
  }).then(r => r.json());

  // Display results
  console.log(result);
}
```

---

## 📁 File Structure

```
Atlas Terminal/V1.1.1/
├── data/
│   ├── metadata.json          # Generated dataset info
│   └── datasets/              # Symlink or data folder
├── backend.py                 # New endpoints added
├── scan_datasets.py           # Metadata generator
└── HOSTED_DATASETS_README.md  # This file
```

---

## 🐛 Troubleshooting

### Issue: "Dataset not found"
**Solution:**
- Check `DATA_ROOT_PATH` environment variable
- Verify the dataset path in metadata.json
- Ensure CSV files exist in Data folder

### Issue: "Metadata file not found"
**Solution:**
```bash
python scan_datasets.py
```

### Issue: Large response times
**Solution:**
- Consider adding caching for frequently accessed datasets
- Use pagination for large datasets
- Implement lazy loading

---

## 📊 Available Datasets

| Instrument | Timeframes Available | Total Size |
|------------|---------------------|------------|
| **EURUSD** | M1, M5, M15, M30, H1, H4, D1 | ~30 MB |
| **GBPUSD** | M1, M5, M15, M30, H1, H4, D1 | ~30 MB |
| **USDJPY** | M1, M5, M15, M30, H1, H4, D1 | ~30 MB |
| **USDCAD** | M1, M5, M15, M30, H1, H4, D1 | ~30 MB |
| **USDCHF** | M1, M5, M15, M30, H1, H4, D1 | ~30 MB |
| **XAUUSD** | M1, M5, M15, M30, H1, H4, D1 | ~35 MB |
| **BTCUSD** | M1, M5, M15, M30, H1, H4, D1 | ~28 MB |
| **US500**  | M1, M5, M15, M30, H1, H4, D1 | ~35 MB |

**Total:** 57 datasets, 240 MB

---

## 🔐 Security Considerations

### For Production:

1. **Authentication**: Add JWT token requirement to dataset endpoints
2. **Rate Limiting**: Prevent abuse of data downloads
3. **Access Control**: Limit which users can access which datasets
4. **Data Encryption**: Encrypt sensitive trading data

### Example (with authentication):

```python
@app.get("/api/datasets")
async def list_datasets(current_user: User = Depends(get_current_active_user)):
    # Only authenticated users can list datasets
    ...
```

---

## 🎯 Roadmap

### Phase 1: Basic Functionality ✅
- [x] API endpoints for listing datasets
- [x] API endpoint to get dataset info
- [x] Basic analysis endpoint

### Phase 2: Frontend Integration 🚧
- [ ] Dropdown selector for datasets
- [ ] Real-time analysis integration
- [ ] Results visualization

### Phase 3: Cloud Deployment 📋
- [ ] Configure cloud storage
- [ ] Upload data to cloud
- [ ] Update backend to fetch from cloud

### Phase 4: Advanced Features 💡
- [ ] Dataset caching
- [ ] Partial dataset loading (pagination)
- [ ] Custom dataset upload
- [ ] Dataset versioning

---

## 📞 Support

For questions or issues:
1. Check the Railway deployment logs
2. Test endpoints locally first
3. Verify Data folder structure matches metadata.json

---

**Atlas Terminal V1.1.2** - Hosted Datasets Feature 🚀
