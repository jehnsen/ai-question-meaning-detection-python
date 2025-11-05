# Business Intelligence & Analytics Dashboard Guide

## Overview

The Effortless-Respond system now includes comprehensive Business Intelligence and Analytics capabilities that provide deep insights into questionnaire processing, answer effectiveness, vendor risk patterns, and system performance.

This feature automatically tracks every question processed, records match methods, similarity scores, and performance metrics, enabling data-driven decision-making and continuous improvement.

---

## Key Features

### 📊 **Dashboard Overview**
- Real-time today's metrics (questionnaires, questions, status breakdown)
- All-time totals and historical data
- Match effectiveness percentages
- Average performance metrics

### 🔍 **Match Method Analysis**
- Breakdown of how questions are being matched
- Distribution across saved links, exact IDs, AI high/medium confidence, and no matches
- System efficiency metrics

### 📈 **Time-Series Trends**
- Daily usage trends over customizable time periods
- Question volume tracking
- Status distribution over time
- Perfect for identifying patterns and growth

### 🏆 **Top Canonical Questions**
- Most frequently matched questions
- Average similarity scores
- Identifies most reusable answers

### 🏢 **Vendor Insights**
- Per-vendor analytics (questionnaires, questions, match rates)
- Processing time comparisons
- Vendor assessment tracking

### 🏭 **Industry Analysis**
- Industry-level aggregations
- Match effectiveness by industry
- Vendor counts per industry

---

## Database Schema

### **AnalyticsEvent Table**

Tracks every question processing event with detailed metadata.

```sql
CREATE TABLE analyticsevent (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Event details
    event_type VARCHAR NOT NULL,              -- "question_matched", "questionnaire_processed"
    questionnaire_id VARCHAR,                 -- Batch identifier
    question_id VARCHAR,                      -- Individual question ID

    -- Result details
    status VARCHAR,                           -- "LINKED", "CONFIRMATION_REQUIRED", "NO_MATCH"
    match_method VARCHAR,                     -- "saved_link", "exact_id", "ai_high_conf", "ai_medium_conf"
    similarity_score FLOAT,                   -- AI similarity score (0-1)

    -- Performance
    processing_time_ms INTEGER,               -- Processing time in milliseconds

    -- Context
    canonical_question_id VARCHAR,            -- Matched canonical question
    vendor_name VARCHAR,                      -- Vendor being assessed
    industry VARCHAR                          -- Vendor industry
);

-- Indexes for fast queries
CREATE INDEX idx_analyticsevent_timestamp ON analyticsevent(timestamp);
CREATE INDEX idx_analyticsevent_event_type ON analyticsevent(event_type);
CREATE INDEX idx_analyticsevent_status ON analyticsevent(status);
CREATE INDEX idx_analyticsevent_vendor ON analyticsevent(vendor_name);
CREATE INDEX idx_analyticsevent_industry ON analyticsevent(industry);
```

### **UsageMetrics Table** (Future Enhancement)

Aggregated daily metrics for faster dashboard queries.

```sql
CREATE TABLE usagemetrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,

    -- Volume metrics
    total_questionnaires INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,

    -- Status breakdown
    linked_count INTEGER DEFAULT 0,
    confirmation_required_count INTEGER DEFAULT 0,
    no_match_count INTEGER DEFAULT 0,

    -- Match method breakdown
    saved_link_count INTEGER DEFAULT 0,
    exact_id_count INTEGER DEFAULT 0,
    ai_high_conf_count INTEGER DEFAULT 0,
    ai_medium_conf_count INTEGER DEFAULT 0,

    -- Performance
    avg_processing_time_ms FLOAT,
    total_processing_time_ms INTEGER DEFAULT 0
);
```

---

## API Endpoints

### 1. **Dashboard Overview**

**GET** `/analytics/dashboard`

Returns comprehensive overview statistics for a CEO dashboard.

**Response:**
```json
{
  "today_questionnaires": 15,
  "today_questions": 450,
  "today_linked": 320,
  "today_confirmation_required": 95,
  "today_no_match": 35,
  "total_questionnaires": 1250,
  "total_questions": 38500,
  "total_response_entries": 850,
  "total_question_links": 12500,
  "linked_percentage": 71.2,
  "confirmation_percentage": 21.3,
  "no_match_percentage": 7.5,
  "avg_processing_time_ms": 45.3
}
```

**Use Cases:**
- Executive dashboard main screen
- Daily standup metrics
- Monthly performance reports

---

### 2. **Match Method Breakdown**

**GET** `/analytics/match-methods`

Shows how questions are being matched (efficiency analysis).

**Response:**
```json
{
  "saved_link": 12500,
  "exact_id": 3200,
  "ai_high_confidence": 8500,
  "ai_medium_confidence": 6800,
  "no_match": 2400,
  "saved_link_pct": 37.5,
  "exact_id_pct": 9.6,
  "ai_high_confidence_pct": 25.5,
  "ai_medium_confidence_pct": 20.4,
  "no_match_pct": 7.2
}
```

**Insights:**
- High `saved_link_pct` = System learning over time (good!)
- High `ai_high_confidence_pct` = AI working well
- High `no_match_pct` = Need more canonical answers

**Use Cases:**
- System efficiency monitoring
- AI performance evaluation
- Identifying need for new canonical answers

---

### 3. **Time-Series Data**

**GET** `/analytics/time-series?days=30`

Returns daily metrics over specified time period (default: 30 days).

**Query Parameters:**
- `days` (optional): Number of days to include (default: 30)

**Response:**
```json
{
  "dates": ["2025-01-01", "2025-01-02", "2025-01-03", "..."],
  "questionnaires": [10, 15, 12, 18, "..."],
  "questions": [300, 450, 360, 540, "..."],
  "linked": [215, 320, 255, 385, "..."],
  "confirmation_required": [65, 95, 75, 115, "..."],
  "no_match": [20, 35, 30, 40, "..."]
}
```

**Use Cases:**
- Line charts showing usage growth
- Trend analysis (daily, weekly, monthly)
- Identifying usage patterns
- Seasonal analysis

**Visualization Example:**
```javascript
// Chart.js example
const chartData = {
  labels: data.dates,
  datasets: [
    { label: 'Linked', data: data.linked, borderColor: 'green' },
    { label: 'Confirmation Required', data: data.confirmation_required, borderColor: 'orange' },
    { label: 'No Match', data: data.no_match, borderColor: 'red' }
  ]
};
```

---

### 4. **Top Canonical Questions**

**GET** `/analytics/top-questions?limit=10`

Returns most frequently matched canonical questions.

**Query Parameters:**
- `limit` (optional): Number of results to return (default: 10)

**Response:**
```json
[
  {
    "question_id": "ISO-27001",
    "question_text": "What are ISO 27001 security controls?",
    "match_count": 450,
    "avg_similarity_score": 0.9156
  },
  {
    "question_id": "GDPR-COMPLIANCE",
    "question_text": "How do you ensure GDPR compliance?",
    "match_count": 380,
    "avg_similarity_score": 0.8923
  },
  {
    "question_id": "MFA-POLICY",
    "question_text": "What is your multi-factor authentication policy?",
    "match_count": 320,
    "avg_similarity_score": 0.9012
  }
]
```

**Insights:**
- High `match_count` = Very reusable answer
- High `avg_similarity_score` = Clear, well-written canonical question
- Low `avg_similarity_score` with high `match_count` = May need answer improvement

**Use Cases:**
- Identifying most valuable canonical answers
- Prioritizing answer quality improvements
- Understanding common vendor questions
- Training AI on best-performing questions

---

### 5. **Vendor Insights**

**GET** `/analytics/vendors?limit=20`

Returns analytics grouped by vendor.

**Query Parameters:**
- `limit` (optional): Number of vendors to return (default: 20)

**Response:**
```json
[
  {
    "vendor_name": "Acme Corp",
    "questionnaire_count": 5,
    "question_count": 450,
    "linked_count": 320,
    "confirmation_required_count": 95,
    "no_match_count": 35,
    "avg_processing_time_ms": 42.5
  },
  {
    "vendor_name": "TechVendor Inc",
    "questionnaire_count": 3,
    "question_count": 280,
    "linked_count": 210,
    "confirmation_required_count": 50,
    "no_match_count": 20,
    "avg_processing_time_ms": 38.2
  }
]
```

**Insights:**
- High `linked_count` = Vendor with standard questions
- High `no_match_count` = Vendor with unique/unusual questions
- High `question_count` = Frequently assessed vendor

**Use Cases:**
- Vendor assessment tracking
- Identifying vendors needing special attention
- Performance comparisons across vendors
- Vendor onboarding optimization

---

### 6. **Industry Analysis**

**GET** `/analytics/industries`

Returns analytics grouped by industry.

**Response:**
```json
[
  {
    "industry": "Healthcare",
    "vendor_count": 25,
    "questionnaire_count": 85,
    "question_count": 8500,
    "avg_linked_percentage": 75.3
  },
  {
    "industry": "Finance",
    "vendor_count": 18,
    "questionnaire_count": 62,
    "question_count": 6200,
    "avg_linked_percentage": 68.5
  },
  {
    "industry": "Technology",
    "vendor_count": 42,
    "questionnaire_count": 150,
    "question_count": 15000,
    "avg_linked_percentage": 82.1
  }
]
```

**Insights:**
- High `avg_linked_percentage` = Industry with standardized questions
- Low `avg_linked_percentage` = Industry needs more canonical answers
- High `vendor_count` = Frequently assessed industry

**Use Cases:**
- Industry-specific compliance tracking
- Benchmark match rates across industries
- Prioritize canonical answer development
- Industry-specific risk analysis

---

## How Analytics Tracking Works

### Automatic Event Logging

The system **does NOT automatically log events yet**. You need to integrate `log_analytics_event()` into your batch processing endpoints.

### Integration Example

Here's how to integrate analytics into the `/batch-process-questionnaire` endpoint:

```python
@app.post("/batch-process-questionnaire", response_model=QuestionnaireOutput)
async def batch_process_questionnaire(
    questionnaire: QuestionnaireInput,
    vendor_name: Optional[str] = None,  # NEW: Optional vendor context
    industry: Optional[str] = None,     # NEW: Optional industry context
    session: Session = Depends(get_session)
):
    # Generate unique questionnaire ID
    questionnaire_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    start_time = time.time()

    results = []

    for question in questionnaire.questions:
        question_start = time.time()

        # Step 1: Check saved link
        existing_link = session.exec(
            select(QuestionLink).where(QuestionLink.new_question_id == question.id)
        ).first()

        if existing_link:
            response_entry = session.get(ResponseEntry, existing_link.linked_response_id)
            if response_entry:
                # LOG ANALYTICS EVENT
                log_analytics_event(
                    session=session,
                    event_type="question_matched",
                    questionnaire_id=questionnaire_id,
                    question_id=question.id,
                    status="LINKED",
                    match_method="saved_link",
                    processing_time_ms=int((time.time() - question_start) * 1000),
                    canonical_question_id=response_entry.question_id,
                    vendor_name=vendor_name,
                    industry=industry
                )

                results.append(QuestionResult(...))
                continue

        # Step 2: Check exact ID match
        exact_match = session.exec(
            select(ResponseEntry).where(ResponseEntry.question_id == question.id)
        ).first()

        if exact_match:
            # LOG ANALYTICS EVENT
            log_analytics_event(
                session=session,
                event_type="question_matched",
                questionnaire_id=questionnaire_id,
                question_id=question.id,
                status="LINKED",
                match_method="exact_id",
                processing_time_ms=int((time.time() - question_start) * 1000),
                canonical_question_id=exact_match.question_id,
                vendor_name=vendor_name,
                industry=industry
            )

            results.append(QuestionResult(...))
            continue

        # Steps 3 & 4: AI search with confidence tiers
        # ... (similar logging for ai_high_conf, ai_medium_conf, no_match)

    # Log questionnaire completion
    total_time = int((time.time() - start_time) * 1000)
    log_analytics_event(
        session=session,
        event_type="questionnaire_processed",
        questionnaire_id=questionnaire_id,
        processing_time_ms=total_time,
        vendor_name=vendor_name,
        industry=industry
    )

    return QuestionnaireOutput(results=results)
```

---

## Testing Analytics

### Prerequisites

1. **Reset Database** (new tables added):
```bash
./venv/Scripts/python reset_database.py 1
```

2. **Start Server**:
```bash
./venv/Scripts/python main.py
```

### Test Data Generation

See `test_analytics.py` (to be created) for comprehensive test suite.

---

## Dashboard Visualization Examples

### Frontend Integration (React Example)

```jsx
import { useEffect, useState } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';

function AnalyticsDashboard() {
  const [overview, setOverview] = useState(null);
  const [timeSeries, setTimeSeries] = useState(null);
  const [matchMethods, setMatchMethods] = useState(null);

  useEffect(() => {
    // Fetch dashboard data
    fetch('http://localhost:8000/analytics/dashboard')
      .then(res => res.json())
      .then(data => setOverview(data));

    fetch('http://localhost:8000/analytics/time-series?days=30')
      .then(res => res.json())
      .then(data => setTimeSeries(data));

    fetch('http://localhost:8000/analytics/match-methods')
      .then(res => res.json())
      .then(data => setMatchMethods(data));
  }, []);

  if (!overview || !timeSeries || !matchMethods) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      {/* Overview Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Today's Questions</h3>
          <div className="stat-value">{overview.today_questions}</div>
          <div className="stat-breakdown">
            <span className="linked">{overview.today_linked} linked</span>
            <span className="confirm">{overview.today_confirmation_required} confirm</span>
            <span className="no-match">{overview.today_no_match} no match</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Match Effectiveness</h3>
          <div className="stat-value">{overview.linked_percentage}%</div>
          <div className="stat-label">Questions Linked</div>
        </div>

        <div className="stat-card">
          <h3>Avg Processing Time</h3>
          <div className="stat-value">{overview.avg_processing_time_ms}ms</div>
          <div className="stat-label">Per Question</div>
        </div>

        <div className="stat-card">
          <h3>Total Canonical Answers</h3>
          <div className="stat-value">{overview.total_response_entries}</div>
          <div className="stat-label">In Knowledge Base</div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div className="chart-container">
        <h2>Usage Trends (Last 30 Days)</h2>
        <Line
          data={{
            labels: timeSeries.dates,
            datasets: [
              {
                label: 'Questions Processed',
                data: timeSeries.questions,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)'
              },
              {
                label: 'Linked',
                data: timeSeries.linked,
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)'
              }
            ]
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false
          }}
        />
      </div>

      {/* Match Methods Pie Chart */}
      <div className="chart-container">
        <h2>Match Method Distribution</h2>
        <Pie
          data={{
            labels: [
              'Saved Links',
              'Exact ID',
              'AI High Confidence',
              'AI Medium Confidence',
              'No Match'
            ],
            datasets: [{
              data: [
                matchMethods.saved_link,
                matchMethods.exact_id,
                matchMethods.ai_high_confidence,
                matchMethods.ai_medium_confidence,
                matchMethods.no_match
              ],
              backgroundColor: [
                '#4CAF50',
                '#2196F3',
                '#FFC107',
                '#FF9800',
                '#F44336'
              ]
            }]
          }}
        />
      </div>
    </div>
  );
}
```

---

## Performance Considerations

### Database Query Optimization

All analytics endpoints use indexed fields for fast queries:
- `timestamp` index for time-range queries
- `event_type` index for filtering event types
- `status` index for status breakdowns
- `vendor_name` and `industry` indexes for grouping

### Caching Strategy (Recommended)

For high-traffic dashboards, implement caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache dashboard overview for 5 minutes
@lru_cache(maxsize=1)
def get_cached_dashboard_overview(cache_key: str):
    # cache_key changes every 5 minutes
    # Implementation here
    pass

@app.get("/analytics/dashboard")
async def get_dashboard_overview(session: Session = Depends(get_session)):
    cache_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")[:-1]  # Round to 5 min
    return get_cached_dashboard_overview(cache_key)
```

### Aggregation Table (Future Enhancement)

For very large datasets (millions of events), implement the `UsageMetrics` table with daily aggregations using a background job:

```python
# Daily aggregation job (run at midnight)
def aggregate_daily_metrics(target_date: datetime):
    # Aggregate all events from target_date
    # Insert into UsageMetrics table
    # Dashboard queries UsageMetrics instead of AnalyticsEvent
    pass
```

---

## Best Practices

### 1. **Always Provide Context**
When calling batch endpoints, include vendor and industry information:
```python
payload = {
    "questions": [...],
    "vendor_name": "Acme Corp",
    "industry": "Healthcare"
}
```

### 2. **Use Unique Questionnaire IDs**
Generate unique IDs for each batch:
```python
questionnaire_id = f"BATCH-{vendor_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

### 3. **Monitor Key Metrics**
Set up alerts for:
- `no_match_percentage` > 15% (need more canonical answers)
- `avg_processing_time_ms` > 100ms (performance issue)
- `confirmation_percentage` > 30% (AI confidence too low)

### 4. **Regular Data Analysis**
Schedule weekly reviews of:
- Top canonical questions (identify gaps)
- Vendor insights (understand usage patterns)
- Industry analysis (industry-specific trends)

---

## Troubleshooting

### Issue: No analytics data showing

**Solution:** Ensure analytics logging is integrated into batch endpoints. Check that `log_analytics_event()` is being called.

### Issue: Slow dashboard queries

**Solution:**
1. Verify database indexes exist
2. Implement caching (see above)
3. Consider daily aggregation for large datasets

### Issue: Missing vendor/industry data

**Solution:** Update API calls to include vendor and industry context parameters.

---

## Roadmap

### Planned Enhancements

1. **Automated Daily Aggregation** - Background job to populate `UsageMetrics` table
2. **Real-time Dashboard** - WebSocket support for live updates
3. **Advanced Filtering** - Filter analytics by date range, vendor, industry
4. **Export Functionality** - CSV/Excel export for reports
5. **Custom Alerts** - Email/Slack notifications for key events
6. **AI Performance Scoring** - Detailed AI accuracy metrics
7. **Cost Analytics** - OpenAI API usage and cost tracking
8. **Anomaly Detection** - Detect unusual patterns automatically

---

## API Reference Summary

| Endpoint | Method | Description | Use Case |
|----------|--------|-------------|----------|
| `/analytics/dashboard` | GET | Overview statistics | CEO dashboard |
| `/analytics/match-methods` | GET | Match method breakdown | System efficiency |
| `/analytics/time-series?days=30` | GET | Daily trends | Usage trends |
| `/analytics/top-questions?limit=10` | GET | Top canonical questions | Answer optimization |
| `/analytics/vendors?limit=20` | GET | Vendor analytics | Vendor tracking |
| `/analytics/industries` | GET | Industry analytics | Industry analysis |

---

## Conclusion

The Business Intelligence & Analytics Dashboard provides powerful insights into your Effortless-Respond system, enabling:

✅ **Data-driven decision making**
✅ **System performance monitoring**
✅ **Answer quality optimization**
✅ **Vendor risk pattern analysis**
✅ **Continuous improvement**

This feature transforms your questionnaire processing system from a black box into a transparent, measurable, and continuously improving platform that CEOs and stakeholders will love!
