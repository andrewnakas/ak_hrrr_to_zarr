# Data Storage Options for Alaska HRRR

## Problem: Zarr Files Are Too Large for GitHub

A single Alaska HRRR forecast cycle (1 init_time × 19 lead_times × 21 variables) generates approximately:
- **Uncompressed**: ~2.2 GB
- **Compressed (zarr)**: ~500 MB - 1 GB

GitHub has strict file size limits:
- **Per file**: 100 MB hard limit
- **Repository**: 1 GB soft limit, 5 GB hard limit

**Zarr stores contain many files**, and even compressed, they exceed GitHub's limits.

## Current Solution: Artifacts Only

The current workflow:
1. ✅ **Generates** Zarr data during workflow runs
2. ✅ **Uploads** to GitHub Actions artifacts (7-day retention)
3. ✅ **Commits** catalog metadata and summaries to git
4. ❌ **Does NOT commit** actual Zarr data arrays to git

### Accessing Data

Data is available through:
- **GitHub Actions Artifacts**: Download from workflow run (7 days)
- **Catalog**: View metadata on GitHub Pages

## Production Solutions

For production deployment, choose one of these options:

### Option 1: Cloud Storage (Recommended)

Store Zarr on cloud storage and reference from catalog:

**AWS S3**:
```bash
# Upload to S3
aws s3 sync data/hrrr_alaska.zarr s3://your-bucket/hrrr_alaska.zarr --storage-class INTELLIGENT_TIERING

# Update catalog to point to S3
# catalog/catalog.json: "zarr_url": "s3://your-bucket/hrrr_alaska.zarr"
```

**Google Cloud Storage**:
```bash
gsutil -m rsync -r data/hrrr_alaska.zarr gs://your-bucket/hrrr_alaska.zarr
```

**Azure Blob Storage**:
```bash
az storage blob upload-batch -s data/hrrr_alaska.zarr -d your-container
```

**Pros**:
- ✅ Unlimited size
- ✅ Fast access
- ✅ Pay only for storage used (~$0.02/GB/month)
- ✅ Works with fsspec for direct access

**Cons**:
- Requires cloud account
- Ongoing costs (minimal)

### Option 2: Git LFS

Use Git Large File Storage for binary data:

```bash
# Install git-lfs
git lfs install

# Track Zarr data files
git lfs track "data/*.zarr/**"
git add .gitattributes

# Commit normally (LFS handles large files)
git add data/
git commit -m "Add Zarr data via LFS"
```

**Pros**:
- ✅ Integrated with GitHub
- ✅ Easy to use

**Cons**:
- Free tier: 1 GB storage, 1 GB bandwidth/month
- Paid: $5/month per 50 GB
- Still limited for continuous updates

### Option 3: External Data Service

Use a data hosting service:

- **Hugging Face Datasets**: Free hosting for open datasets
- **Zenodo**: Free, citable DOIs for research data
- **Pangeo Forge**: Cloud-native data pipelines
- **Source Cooperative**: Geospatial data hosting

### Option 4: Incremental Zarr

Instead of storing all data, keep rolling window:

```python
# Keep only last N days
max_days = 7
cutoff = datetime.now() - timedelta(days=max_days)

ds = xr.open_zarr("data/hrrr_alaska.zarr")
recent = ds.sel(init_time=slice(cutoff, None))
recent.to_zarr("data/hrrr_alaska.zarr", mode="w")
```

**Pros**:
- ✅ Smaller size
- ✅ Can fit in GitHub

**Cons**:
- Only keeps recent data
- Loses historical forecasts

## Recommended Setup

For this project, I recommend:

**Development/Testing**:
- Use GitHub Actions artifacts (current setup)
- Data available for 7 days
- No additional costs

**Production**:
1. **Set up S3 bucket** (or equivalent)
2. **Update workflow** to sync Zarr to S3 after creation
3. **Update catalog** to reference S3 URL
4. **Keep git lean** with metadata only

### Example Production Workflow

```yaml
- name: Upload to S3
  run: |
    aws s3 sync data/hrrr_alaska.zarr \
      s3://${{ secrets.S3_BUCKET }}/hrrr_alaska/$(date +%Y%m%d_%H)/ \
      --storage-class INTELLIGENT_TIERING
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1
```

## Cost Estimates

**S3 Storage** (Intelligent Tiering):
- Single forecast: ~500 MB
- 8 forecasts/day: ~4 GB/day
- 30 days retention: ~120 GB
- **Cost**: ~$2.40/month + minimal access fees

**GitHub Actions**:
- Workflow time: ~10 min/run × 8 runs/day
- Public repos: **Free** (2,000 min/month free)
- **Cost**: $0

**Total monthly cost**: ~$2-3 for production S3 storage

## Migration Path

1. **Start**: Use artifacts (current setup) ✅
2. **Test**: Verify data pipeline works
3. **Deploy**: Set up S3/cloud storage
4. **Update**: Modify workflow for cloud upload
5. **Optimize**: Add retention policies, tiering

## Current Status

- ✅ Data generated successfully in workflows
- ✅ Catalog metadata committed to git
- ✅ Data available as artifacts (7 days)
- 📋 TODO: Set up cloud storage for production
