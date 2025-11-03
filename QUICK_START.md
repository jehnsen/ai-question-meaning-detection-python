# Quick Start Guide

## Application is Running!

Your Effortless-Respond API is now running at:

- **API Base URL**: http://localhost:8001
- **Interactive Docs**: http://localhost:8001/docs
- **Alternative Docs**: http://localhost:8001/redoc

## Test the API

### Option 1: Use the Interactive Docs (Recommended)

Open http://localhost:8001/docs in your browser to test all endpoints with a nice UI.

### Option 2: Use curl

#### 1. Create your first response

```bash
curl -X POST "http://localhost:8001/create-new-response" ^
  -H "Content-Type: application/json" ^
  -d "{\"question_text\": \"What are ISO 27001 security controls?\", \"answer_text\": \"ISO 27001 specifies 114 security controls organized in 14 categories.\", \"evidence\": \"ISO 27001:2013 Annex A\"}"
```

#### 2. Process a similar question

```bash
curl -X POST "http://localhost:8001/process-question" ^
  -H "Content-Type: application/json" ^
  -d "{\"question_text\": \"What security controls does ISO 27001 have?\"}"
```

You should get a `confirmation_required` response with suggestions!

#### 3. Confirm the suggestion

```bash
curl -X POST "http://localhost:8001/create-link" ^
  -H "Content-Type: application/json" ^
  -d "{\"new_question_text\": \"What security controls does ISO 27001 have?\", \"confirmed_response_id\": 1}"
```

#### 4. Process the same question again

```bash
curl -X POST "http://localhost:8001/process-question" ^
  -H "Content-Type: application/json" ^
  -d "{\"question_text\": \"What security controls does ISO 27001 have?\"}"
```

Now it returns `status: "linked"` immediately!

### Option 3: Use PowerShell

```powershell
# Create a new response
Invoke-RestMethod -Uri "http://localhost:8001/create-new-response" -Method Post -ContentType "application/json" -Body '{"question_text": "What are GDPR requirements?", "answer_text": "GDPR requires data protection by design and by default.", "evidence": "GDPR Article 25"}'

# Process a question
Invoke-RestMethod -Uri "http://localhost:8001/process-question" -Method Post -ContentType "application/json" -Body '{"question_text": "What does GDPR require?"}'
```

## View All Data

```bash
# List all responses
curl http://localhost:8001/responses

# List all links
curl http://localhost:8001/links
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /process-question | Main endpoint - find answers |
| POST | /create-link | Confirm a suggestion |
| POST | /create-new-response | Add new answer |
| GET | /responses | List all responses |
| GET | /links | List all links |
| DELETE | /responses/{id} | Delete a response |
| DELETE | /links/{id} | Delete a link |

## Stopping the Application

The application is running in the background. To stop it:

1. Find the process:
   - Windows: Task Manager > Find "python.exe" running uvicorn
   - Or: `tasklist | findstr python`

2. Kill the process:
   - `taskkill /F /PID <process_id>`

Or simply close the terminal.

## Troubleshooting

### Port Already in Use

If port 8001 is also in use, edit the command in the terminal to use a different port:

```bash
./venv/Scripts/python -c "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8002)"
```

### Database Connection Issues

Run the test script:

```bash
./venv/Scripts/python test_setup.py
```

## Next Steps

1. Open http://localhost:8001/docs
2. Try the examples above
3. Build your own questions and answers database
4. Integrate with your application via the REST API

Enjoy using Effortless-Respond!
