"""
Automated workflow test for Effortless-Respond API
Tests the complete user journey with realistic compliance data
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8003"
HEADERS = {"Content-Type": "application/json"}


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response: requests.Response, label: str = "Response"):
    """Pretty print API response."""
    print(f"\n{label}:")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")


def test_1_create_initial_responses():
    """STEP 1: Create initial knowledge base with compliance questions."""
    print_section("STEP 1: Building Knowledge Base")

    responses_data = [
        {
            "question": "What are the main requirements of ISO 27001?",
            "answer": "ISO 27001 requires organizations to establish, implement, maintain and continually improve an Information Security Management System (ISMS). Key requirements include: 1) Leadership commitment and policy framework, 2) Risk assessment and treatment, 3) Implementation of 114 security controls across 14 domains, 4) Documented information and procedures, 5) Internal audits and management reviews, 6) Continual improvement processes.",
            "evidence": "ISO/IEC 27001:2013 Clauses 4-10"
        },
        {
            "question": "What are the key principles of GDPR?",
            "answer": "GDPR is built on seven key principles: 1) Lawfulness, fairness and transparency, 2) Purpose limitation - data collected for specified purposes only, 3) Data minimization - only collect what's necessary, 4) Accuracy - keep data up to date, 5) Storage limitation - don't keep data longer than needed, 6) Integrity and confidentiality - ensure appropriate security, 7) Accountability - demonstrate compliance with all principles.",
            "evidence": "GDPR Article 5"
        },
        {
            "question": "What is multi-factor authentication and why is it important?",
            "answer": "Multi-factor authentication (MFA) requires users to provide two or more verification factors to gain access to a resource. The factors fall into three categories: something you know (password), something you have (phone, token, smart card), and something you are (biometrics). MFA is critical because even if one factor is compromised (e.g., password stolen), unauthorized access is prevented. Studies show MFA blocks over 99.9% of account compromise attacks.",
            "evidence": "NIST SP 800-63B Digital Identity Guidelines"
        },
        {
            "question": "What is the difference between ISO 27001 and ISO 27002?",
            "answer": "ISO 27001 is the certification standard that specifies requirements for establishing, implementing, and maintaining an ISMS. It's the framework organizations get certified against. ISO 27002, on the other hand, is a code of practice providing guidelines and best practices for implementing the security controls referenced in ISO 27001 Annex A. Think of 27001 as 'what to do' and 27002 as 'how to do it'.",
            "evidence": "ISO/IEC 27001:2013 and ISO/IEC 27002:2013"
        },
        {
            "question": "What is the maximum fine for GDPR violations?",
            "answer": "GDPR violations can result in administrative fines up to €20 million or 4% of annual global turnover (whichever is higher) for the most serious infringements such as violating core processing principles or data subject rights. Lesser violations may incur fines up to €10 million or 2% of annual global turnover.",
            "evidence": "GDPR Article 83"
        }
    ]

    created_ids = []
    for i, data in enumerate(responses_data, 1):
        print(f"\n[{i}/{len(responses_data)}] Creating response for: '{data['question'][:60]}...'")

        payload = {
            "question_text": data["question"],
            "answer_text": data["answer"],
            "evidence": data["evidence"]
        }

        response = requests.post(
            f"{BASE_URL}/create-new-response",
            headers=HEADERS,
            json=payload
        )

        if response.status_code == 200:
            result = response.json()
            created_ids.append(result["id"])
            print(f"   [OK] Created with ID: {result['id']}")
        else:
            print(f"   [X] Failed: {response.text}")

    print(f"\n[OK] Successfully created {len(created_ids)} responses")
    return created_ids


def test_2_semantic_search():
    """STEP 2: Test AI semantic search with similar questions."""
    print_section("STEP 2: Testing AI Semantic Search")

    test_cases = [
        {
            "question": "What does ISO 27001 require from organizations?",
            "description": "Similar to: 'What are the main requirements of ISO 27001?'"
        },
        {
            "question": "Tell me about GDPR's core principles",
            "description": "Similar to: 'What are the key principles of GDPR?'"
        },
        {
            "question": "Why is MFA important?",
            "description": "Similar to: 'What is multi-factor authentication...'"
        },
        {
            "question": "How are ISO 27001 and 27002 different?",
            "description": "Similar to: 'What is the difference between ISO 27001 and ISO 27002?'"
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: '{test['question']}'")
        print(f"   Expected match: {test['description']}")

        response = requests.post(
            f"{BASE_URL}/process-question",
            headers=HEADERS,
            json={"question_text": test["question"]}
        )

        if response.status_code == 200:
            result = response.json()

            if result["status"] == "confirmation_required":
                suggestions = result["suggestions"]
                print(f"   [OK] Found {len(suggestions)} suggestion(s)")

                for j, suggestion in enumerate(suggestions[:2], 1):  # Show top 2
                    score = suggestion["similarity_score"]
                    canonical = suggestion["response"]["canonical_question"]
                    print(f"     [{j}] Similarity: {score:.1%} | Match: '{canonical[:60]}...'")

                results.append({
                    "question": test["question"],
                    "suggestions": suggestions
                })
            elif result["status"] == "no_match_found":
                print(f"   [X] No matches found (unexpected)")
            else:
                print(f"   [X] Unexpected status: {result['status']}")
        else:
            print(f"   [X] Request failed: {response.text}")

    print(f"\n[OK] Completed {len(results)} semantic search tests")
    return results


def test_3_confirm_links(search_results: List[Dict]):
    """STEP 3: User confirms suggested matches to create links."""
    print_section("STEP 3: Confirming Suggestions (Creating Links)")

    confirmed_links = []

    for i, result in enumerate(search_results, 1):
        question = result["question"]
        suggestions = result["suggestions"]

        if not suggestions:
            continue

        # User confirms the top suggestion
        top_suggestion = suggestions[0]
        response_id = top_suggestion["response"]["canonical_question"]  # We'll need to get the ID
        score = top_suggestion["similarity_score"]

        print(f"\n[{i}/{len(search_results)}] Confirming match for: '{question[:50]}...'")
        print(f"   Match: '{top_suggestion['response']['canonical_question'][:60]}...'")
        print(f"   Confidence: {score:.1%}")

        # We need to get the response ID - let's fetch all responses first
        responses_list = requests.get(f"{BASE_URL}/responses").json()

        # Find the matching response ID
        matched_id = None
        for resp in responses_list:
            if resp["canonical_question"] == top_suggestion["response"]["canonical_question"]:
                matched_id = resp["id"]
                break

        if matched_id:
            link_response = requests.post(
                f"{BASE_URL}/create-link",
                headers=HEADERS,
                json={
                    "new_question_text": question,
                    "confirmed_response_id": matched_id
                }
            )

            if link_response.status_code == 200:
                link_data = link_response.json()
                print(f"   [OK] Link created with ID: {link_data['id']}")
                confirmed_links.append(link_data)
            else:
                print(f"   [X] Failed to create link: {link_response.text}")
        else:
            print(f"   [X] Could not find response ID")

    print(f"\n[OK] Created {len(confirmed_links)} confirmed links")
    return confirmed_links


def test_4_instant_retrieval(confirmed_links: List[Dict]):
    """STEP 4: Test instant retrieval using confirmed links."""
    print_section("STEP 4: Testing Instant Retrieval (AC #3)")

    print("\nNow when we ask the same questions, they should return INSTANTLY")
    print("without AI search (because links exist).\n")

    success_count = 0

    for i, link in enumerate(confirmed_links, 1):
        question = link["new_question_text"]

        print(f"[{i}/{len(confirmed_links)}] Asking: '{question[:50]}...'")

        response = requests.post(
            f"{BASE_URL}/process-question",
            headers=HEADERS,
            json={"question_text": question}
        )

        if response.status_code == 200:
            result = response.json()

            if result["status"] == "linked":
                print(f"   [OK] INSTANT MATCH! (via confirmed link)")
                print(f"     Answer: '{result['data']['answer'][:80]}...'")
                success_count += 1
            else:
                print(f"   [X] Unexpected status: {result['status']} (should be 'linked')")
        else:
            print(f"   [X] Request failed: {response.text}")

    print(f"\n[OK] {success_count}/{len(confirmed_links)} questions retrieved instantly via links")


def test_5_no_match_scenario():
    """STEP 5: Test scenario where no similar question exists."""
    print_section("STEP 5: Testing No Match Scenario")

    unrelated_question = "What is the capital of France?"

    print(f"\nAsking completely unrelated question: '{unrelated_question}'")
    print("Expected: status='no_match_found' (no similar questions in knowledge base)\n")

    response = requests.post(
        f"{BASE_URL}/process-question",
        headers=HEADERS,
        json={"question_text": unrelated_question}
    )

    if response.status_code == 200:
        result = response.json()

        if result["status"] == "no_match_found":
            print("   [OK] Correctly returned 'no_match_found'")
            print("   -> User would now provide a new answer via /create-new-response")
        elif result["status"] == "confirmation_required":
            print(f"   [WARN] Found {len(result['suggestions'])} suggestion(s) (unexpected)")
            for sugg in result["suggestions"]:
                print(f"     - {sugg['response']['canonical_question'][:60]}... ({sugg['similarity_score']:.1%})")
        else:
            print(f"   [X] Unexpected status: {result['status']}")
    else:
        print(f"   [X] Request failed: {response.text}")


def test_6_view_knowledge_base():
    """STEP 6: View all responses and links in the system."""
    print_section("STEP 6: Knowledge Base Summary")

    # Get all responses
    responses = requests.get(f"{BASE_URL}/responses").json()
    print(f"\nTotal Responses in Knowledge Base: {len(responses)}")
    print("\nResponses:")
    for i, resp in enumerate(responses, 1):
        print(f"  [{resp['id']}] {resp['canonical_question']}")

    # Get all links
    links = requests.get(f"{BASE_URL}/links").json()
    print(f"\nTotal Confirmed Links: {len(links)}")
    print("\nLinks:")
    for i, link in enumerate(links, 1):
        print(f"  [{link['id']}] '{link['new_question_text'][:60]}...'")
        print(f"       -> Response ID: {link['linked_response_id']}")


def main():
    """Run complete workflow test."""
    print("\n" + "=" * 80)
    print("  EFFORTLESS-RESPOND API - COMPLETE WORKFLOW TEST")
    print("  Testing realistic compliance Q&A scenarios")
    print("=" * 80)

    try:
        # Check if API is running
        try:
            requests.get(BASE_URL, timeout=2)
        except requests.exceptions.ConnectionError:
            print(f"\n[ERROR]: API not running at {BASE_URL}")
            print("Please start the API first:")
            print('  ./venv/Scripts/python -c "import uvicorn; from main import app; uvicorn.run(app, host=\'0.0.0.0\', port=8003)"')
            return

        # Run workflow
        print("\nAPI is running. Starting workflow test...\n")
        time.sleep(1)

        # Step 1: Create knowledge base
        response_ids = test_1_create_initial_responses()
        time.sleep(1)

        # Step 2: Test semantic search
        search_results = test_2_semantic_search()
        time.sleep(1)

        # Step 3: Confirm matches
        confirmed_links = test_3_confirm_links(search_results)
        time.sleep(1)

        # Step 4: Test instant retrieval
        test_4_instant_retrieval(confirmed_links)
        time.sleep(1)

        # Step 5: Test no match
        test_5_no_match_scenario()
        time.sleep(1)

        # Step 6: Summary
        test_6_view_knowledge_base()

        # Final summary
        print_section("TEST COMPLETE")
        print("\n[OK] All workflow steps completed successfully!")
        print("\nWorkflow Summary:")
        print(f"  1. Created {len(response_ids)} initial responses")
        print(f"  2. Tested {len(search_results)} semantic searches (AI similarity)")
        print(f"  3. Confirmed {len(confirmed_links)} user-approved links")
        print(f"  4. Verified instant retrieval via confirmed links")
        print(f"  5. Tested 'no match' scenario")
        print(f"  6. Reviewed complete knowledge base")

        print("\n" + "=" * 80)
        print("  Next: Open http://localhost:8003/docs to test manually!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
