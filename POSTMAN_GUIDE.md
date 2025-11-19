# Postman Collection Guide - Effortless-Respond API v5.0

## 📦 Files Included

1. **Effortless-Respond-API-v5.postman_collection.json** - Complete API collection
2. **Effortless-Respond-Local.postman_environment.json** - Local environment

## 🚀 Quick Start

### Import into Postman
1. Open Postman
2. Click Import (top left)
3. Import both JSON files
4. Select "Effortless-Respond v5.0 - Local" environment

### Test the Collection
1. Start server: `uvicorn main:app --reload`
2. Run: "Get API Info" → Should show version 5.0.0
3. Run: "Batch Create Responses" → Creates test data
4. Run: "Batch Process" → Tests fallback chain

## 📂 Collection Overview

### Main Endpoints
- **Batch Create Responses** - Create canonical Q&A pairs
- **Batch Process** - Process questions with Intelligent Fallback Chain
- **List Question Links** - View auto-created links

### Test Cases
- ID Match Test
- Fuzzy Match Test (typos)
- Semantic Search Test

## Environment Variables
- `base_url`: http://localhost:8000
- `vendor_id`: vendor1

For complete documentation, see API_GUIDE_V5.md
