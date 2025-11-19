# Example Test Data - 5 Vendors with 100 Questionnaires Each

This directory contains realistic test data for the Effortless-Respond API v5.0.

## Files

Complete test data for 5 vendors, each with 100 comprehensive security and compliance questions (500 total Q&A pairs).

### File Structure

```
example_batch_create.json       - Vendor 1: ACME Corporation (100 questions)
example_data_techstart_inc.json - Vendor 2: TechStart Inc. (100 questions)
example_data_globalbank_ltd.json - Vendor 3: GlobalBank Limited (100 questions)
example_data_healthsys_io.json  - Vendor 4: HealthSys.io (100 questions)
example_data_retailmax_com.json - Vendor 5: RetailMax.com (100 questions)
```

### Vendor Industry Focus

Each vendor file contains industry-specific variations in their answers:

1. **ACME Corporation** (`example_batch_create.json`) - General technology company with comprehensive security controls
2. **TechStart Inc.** (`example_data_techstart_inc.json`) - Modern SaaS startup with cloud-native architecture and advanced security practices
3. **GlobalBank Limited** (`example_data_globalbank_ltd.json`) - Financial services institution with banking regulations, PCI DSS, and extensive compliance requirements
4. **HealthSys.io** (`example_data_healthsys_io.json`) - Healthcare technology provider with HIPAA compliance, patient data protection, and medical device security
5. **RetailMax.com** (`example_data_retailmax_com.json`) - E-commerce platform with PCI DSS Level 1 compliance, payment security, and customer data protection

## Usage

### Load All Vendors

Load all 5 vendors into the database:

```bash
# Load ACME Corporation
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_batch_create.json

# Load TechStart Inc.
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_data_techstart_inc.json

# Load GlobalBank Limited
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_data_globalbank_ltd.json

# Load HealthSys.io
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_data_healthsys_io.json

# Load RetailMax.com
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_data_retailmax_com.json
```

### Load Single Vendor

To load just one vendor for testing:

```bash
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d @example_batch_create.json
```

## Vendor IDs

All vendor IDs are included in the test data files:
- `acme_corp` - ACME Corporation
- `techstart_inc` - TechStart Inc.
- `globalbank_ltd` - GlobalBank Limited
- `healthsys_io` - HealthSys.io
- `retailmax_com` - RetailMax.com

## Data Coverage

The 100 questions cover:

### Security & Compliance (Q001-Q031)
- ISO 27001, SOC 2, GDPR compliance
- Encryption standards
- MFA, access control
- Backup and DR
- Penetration testing
- Incident response

### Infrastructure & Operations (Q032-Q060)
- Ransomware protection
- Code review practices
- API security
- Bug bounty programs
- Email security
- Cryptographic key management
- Physical security
- Mobile device security

### Advanced Security (Q061-Q090)
- Red team exercises
- Privileged access management
- Security metrics and KPIs
- Container security
- Kubernetes security
- Zero trust architecture
- Insider threat detection
- Security automation

### Governance & Compliance (Q091-Q100)
- Secure disposal procedures
- Dependency security
- Security SLAs
- Staff certifications
- CI/CD security
- Infrastructure as code
- Regulatory compliance
- Security incident history

## Using with Postman

1. Import the Postman collection: `Effortless-Respond-API-v5.postman_collection.json`
2. Use the "Batch Create Responses" request
3. In the request body, paste the contents from any vendor file (e.g., `example_batch_create.json`)
4. Click Send
5. Repeat for each vendor file to load all test data

## Testing the Intelligent Fallback Chain

After loading the data, test the fallback chain:

### Test ID Match
```json
{
  "vendor_id": "acme_corp",
  "questions": [
    {"id": "Q001", "text": "Different question but same ID"}
  ]
}
```
Expected: LINKED via ID match

### Test Fuzzy Match  
```json
{
  "vendor_id": "acme_corp",
  "questions": [
    {"id": 9999, "text": "Do u have ISO 27001 certifiction?"}
  ]
}
```
Expected: LINKED via fuzzy match (typos: "u" vs "you", "certifiction" vs "certification")

### Test Semantic Search
```json
{
  "vendor_id": "acme_corp",
  "questions": [
    {"id": 8888, "text": "Are you ISO 27001 compliant?"}
  ]
}
```
Expected: LINKED or CONFIRMATION_REQUIRED via semantic search

## Performance Testing

The 500 total questions (100 per vendor × 5 vendors) are ideal for testing:

- **Batch processing performance**
- **Multi-tenant data isolation**
- **Cost optimization** (Steps 1 & 2 should handle most matches)
- **Match logging analytics**
- **Confidence score distribution**
- **Cross-vendor similarity detection**

### Expected Distribution (Per Vendor)
- ~10-15% ID matches (if you reuse question IDs)
- ~20-30% Fuzzy matches (similar wording)
- ~50-60% Semantic matches (AI-powered)
- ~5-10% No matches

### Cost Analysis (Per Vendor)
- Old v4.0: 100 questions × $0.002 = $0.20
- New v5.0: ~60 questions × $0.002 = $0.12 (40% savings)

### Total System Performance
- **Total Questions**: 500 (5 vendors × 100 questions)
- **Total Cost (v4.0)**: $1.00
- **Total Cost (v5.0)**: ~$0.60 (40% savings)
- **Multi-tenant isolation**: All vendors have separate data with no cross-vendor access

## Testing Multi-Tenant Functionality

With all 5 vendors loaded, you can test:

1. **Data Isolation**: Query questions for one vendor, verify no results from other vendors
2. **Industry-Specific Matching**: Different industries may have similar questions but different answers
3. **Vendor-Specific Analytics**: MatchLog tracks metrics per vendor_id
4. **Cross-Vendor Comparison**: Compare security postures across different industries

## Realistic Data

All questions and answers are based on:
- Real security questionnaires
- Common vendor assessment forms
- Industry-standard compliance frameworks
- Best practices from NIST, OWASP, ISO, SOC 2, GDPR, HIPAA, PCI DSS

### Industry-Specific Compliance Focus

Each vendor file reflects realistic compliance requirements for their industry:

**ACME Corporation (Technology)**
- ISO 27001, SOC 2, GDPR, CCPA
- General cloud security and DevSecOps practices

**TechStart Inc. (SaaS Startup)**
- Modern cloud-native architecture (AWS, GCP)
- Advanced security automation and DevSecOps
- Zero trust architecture and container security

**GlobalBank Limited (Financial Services)**
- Basel III, PCI DSS Level 1, GLBA, FFIEC
- Banking-specific security controls
- Financial regulatory compliance

**HealthSys.io (Healthcare)**
- HIPAA Security & Privacy Rules, HITRUST CSF
- Patient health information (PHI) protection
- Medical device security and FDA guidance

**RetailMax.com (E-Commerce)**
- PCI DSS v4.0 Level 1 Merchant
- Payment card data protection
- E-commerce fraud prevention

This ensures the test data closely resembles production usage across different industries.
