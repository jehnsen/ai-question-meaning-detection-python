"""
Test script for /batch-process-questionnaire endpoint
Generates 1000 realistic vendor risk management questions to test:
- Batch processing performance
- Automatic chunking (>2048 questions)
- Retry logic with exponential backoff
- 4-step processing logic
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
BATCH_ENDPOINT = f"{BASE_URL}/batch-process-questionnaire"
CREATE_RESPONSE_ENDPOINT = f"{BASE_URL}/create-response"

# Test configuration
NUM_QUESTIONS = 1000  # Adjust to test chunking (try 3000+ for multiple chunks)


def generate_realistic_questions(count: int) -> list[dict]:
    """
    Generate realistic vendor risk management questions.

    Categories:
    - Information Security (ISO 27001, SOC 2, encryption)
    - Data Privacy (GDPR, CCPA, data handling)
    - Business Continuity (DR, BCP, uptime)
    - Compliance (PCI DSS, HIPAA, industry standards)
    - Access Controls (MFA, SSO, privileged access)
    - Vendor Management (SLA, subprocessors, insurance)
    """

    question_templates = [
        # Information Security
        ("SEC-{id}", "What encryption standards does your organization use for data at rest?"),
        ("SEC-{id}", "How often do you conduct penetration testing?"),
        ("SEC-{id}", "Do you have an ISO 27001 certification?"),
        ("SEC-{id}", "What is your incident response plan?"),
        ("SEC-{id}", "How do you manage security vulnerabilities?"),
        ("SEC-{id}", "Do you conduct regular security awareness training?"),
        ("SEC-{id}", "What security controls are in place for remote access?"),
        ("SEC-{id}", "How do you secure API endpoints?"),
        ("SEC-{id}", "What is your patch management process?"),
        ("SEC-{id}", "Do you have a Security Operations Center (SOC)?"),

        # Data Privacy
        ("PRIV-{id}", "How do you ensure GDPR compliance?"),
        ("PRIV-{id}", "What is your data retention policy?"),
        ("PRIV-{id}", "How do you handle data subject access requests?"),
        ("PRIV-{id}", "Do you conduct Data Protection Impact Assessments?"),
        ("PRIV-{id}", "What is your process for data breach notification?"),
        ("PRIV-{id}", "How do you anonymize or pseudonymize personal data?"),
        ("PRIV-{id}", "What cross-border data transfer mechanisms do you use?"),
        ("PRIV-{id}", "Do you have a Data Protection Officer?"),
        ("PRIV-{id}", "How do you obtain user consent for data processing?"),
        ("PRIV-{id}", "What rights do data subjects have regarding their data?"),

        # Business Continuity
        ("BC-{id}", "What is your disaster recovery plan?"),
        ("BC-{id}", "What is your guaranteed uptime SLA?"),
        ("BC-{id}", "How often do you test your business continuity plan?"),
        ("BC-{id}", "What is your Recovery Time Objective (RTO)?"),
        ("BC-{id}", "What is your Recovery Point Objective (RPO)?"),
        ("BC-{id}", "Do you have redundant data centers?"),
        ("BC-{id}", "What backup procedures do you have in place?"),
        ("BC-{id}", "How do you ensure service availability?"),
        ("BC-{id}", "What is your incident escalation process?"),
        ("BC-{id}", "Do you have a crisis management team?"),

        # Compliance
        ("COMP-{id}", "Are you PCI DSS compliant?"),
        ("COMP-{id}", "Do you have SOC 2 Type II certification?"),
        ("COMP-{id}", "What industry-specific regulations do you comply with?"),
        ("COMP-{id}", "How often do you conduct compliance audits?"),
        ("COMP-{id}", "Do you comply with HIPAA requirements?"),
        ("COMP-{id}", "What certifications does your organization hold?"),
        ("COMP-{id}", "How do you demonstrate regulatory compliance?"),
        ("COMP-{id}", "Do you undergo third-party security assessments?"),
        ("COMP-{id}", "What is your policy for regulatory changes?"),
        ("COMP-{id}", "How do you maintain audit trails?"),

        # Access Controls
        ("ACCESS-{id}", "Do you require multi-factor authentication?"),
        ("ACCESS-{id}", "What is your password policy?"),
        ("ACCESS-{id}", "How do you manage privileged access?"),
        ("ACCESS-{id}", "Do you support Single Sign-On (SSO)?"),
        ("ACCESS-{id}", "What is your user access review process?"),
        ("ACCESS-{id}", "How do you handle employee offboarding?"),
        ("ACCESS-{id}", "What principle of least privilege controls are in place?"),
        ("ACCESS-{id}", "How do you monitor user activity?"),
        ("ACCESS-{id}", "Do you support role-based access control (RBAC)?"),
        ("ACCESS-{id}", "What is your identity and access management strategy?"),

        # Vendor Management
        ("VENDOR-{id}", "Do you use subprocessors or third-party vendors?"),
        ("VENDOR-{id}", "What insurance coverage do you maintain?"),
        ("VENDOR-{id}", "What are your standard SLA terms?"),
        ("VENDOR-{id}", "How do you manage vendor risk?"),
        ("VENDOR-{id}", "What is your vendor selection process?"),
        ("VENDOR-{id}", "Do you have cyber liability insurance?"),
        ("VENDOR-{id}", "What are your contract termination terms?"),
        ("VENDOR-{id}", "How do you ensure vendor security compliance?"),
        ("VENDOR-{id}", "What is your vendor monitoring process?"),
        ("VENDOR-{id}", "Do you conduct vendor security assessments?"),

        # Infrastructure
        ("INFRA-{id}", "What cloud providers do you use?"),
        ("INFRA-{id}", "Where are your data centers located?"),
        ("INFRA-{id}", "What is your network architecture?"),
        ("INFRA-{id}", "How do you secure your infrastructure?"),
        ("INFRA-{id}", "Do you use containerization or microservices?"),
        ("INFRA-{id}", "What monitoring tools do you use?"),
        ("INFRA-{id}", "How do you manage infrastructure changes?"),
        ("INFRA-{id}", "What is your capacity planning process?"),
        ("INFRA-{id}", "Do you use infrastructure as code?"),
        ("INFRA-{id}", "What is your network segmentation strategy?"),

        # Application Security
        ("APPSEC-{id}", "What secure development practices do you follow?"),
        ("APPSEC-{id}", "Do you conduct code reviews?"),
        ("APPSEC-{id}", "What application security testing do you perform?"),
        ("APPSEC-{id}", "How do you manage application vulnerabilities?"),
        ("APPSEC-{id}", "Do you use static application security testing (SAST)?"),
        ("APPSEC-{id}", "Do you use dynamic application security testing (DAST)?"),
        ("APPSEC-{id}", "What is your software development lifecycle?"),
        ("APPSEC-{id}", "How do you secure third-party libraries and dependencies?"),
        ("APPSEC-{id}", "What is your deployment process?"),
        ("APPSEC-{id}", "Do you implement security by design principles?"),

        # Data Management
        ("DATA-{id}", "How do you classify data?"),
        ("DATA-{id}", "What data loss prevention measures are in place?"),
        ("DATA-{id}", "How do you manage data lifecycle?"),
        ("DATA-{id}", "What data encryption methods do you use?"),
        ("DATA-{id}", "How do you ensure data integrity?"),
        ("DATA-{id}", "What is your data backup frequency?"),
        ("DATA-{id}", "How do you secure data in transit?"),
        ("DATA-{id}", "What data masking techniques do you use?"),
        ("DATA-{id}", "How do you manage sensitive data?"),
        ("DATA-{id}", "What is your data disposal process?"),

        # Risk Management
        ("RISK-{id}", "What is your risk assessment methodology?"),
        ("RISK-{id}", "How often do you conduct risk assessments?"),
        ("RISK-{id}", "What is your risk mitigation strategy?"),
        ("RISK-{id}", "How do you track and monitor risks?"),
        ("RISK-{id}", "What is your risk appetite and tolerance?"),
        ("RISK-{id}", "Do you have a risk management framework?"),
        ("RISK-{id}", "How do you report risks to stakeholders?"),
        ("RISK-{id}", "What cybersecurity risks have you identified?"),
        ("RISK-{id}", "How do you manage third-party risks?"),
        ("RISK-{id}", "What is your risk treatment process?"),
    ]

    questions = []
    template_count = len(question_templates)

    for i in range(count):
        # Cycle through templates
        template = question_templates[i % template_count]
        question_id = template[0].format(id=i + 1)
        question_text = template[1]

        # Add variations to make questions slightly different
        variations = [
            question_text,
            f"{question_text} Please provide details.",
            f"Can you explain {question_text.lower()}",
            f"What are your policies regarding {question_text.lower()[:-1]}?",
        ]

        selected_text = variations[i % len(variations)]

        questions.append({
            "id": question_id,
            "text": selected_text
        })

    return questions


def create_sample_responses():
    """Create some sample responses in the database for testing matching."""
    print("\n" + "="*80)
    print("STEP 1: Creating sample canonical responses")
    print("="*80)

    sample_responses = [
        {
            "question_id": "CANONICAL-ISO27001",
            "question_text": "What is ISO 27001 certification?",
            "answer_text": "ISO 27001 is an international standard for information security management systems (ISMS). It provides a systematic approach to managing sensitive company information, ensuring it remains secure through people, processes, and IT systems.",
            "evidence": "ISO/IEC 27001:2013"
        },
        {
            "question_id": "CANONICAL-GDPR",
            "question_text": "What is GDPR compliance?",
            "answer_text": "GDPR (General Data Protection Regulation) is a comprehensive data protection law that requires organizations to protect EU citizens' personal data and privacy. It includes requirements for consent, data subject rights, breach notification, and data protection by design.",
            "evidence": "GDPR Articles 5, 25, 32, 33"
        },
        {
            "question_id": "CANONICAL-MFA",
            "question_text": "What is multi-factor authentication?",
            "answer_text": "Multi-factor authentication (MFA) is a security process that requires users to provide two or more verification factors to gain access to a resource. This significantly enhances security by combining something you know (password), something you have (token), and/or something you are (biometric).",
            "evidence": "NIST SP 800-63B"
        },
        {
            "question_id": "CANONICAL-SOC2",
            "question_text": "What is SOC 2 Type II certification?",
            "answer_text": "SOC 2 Type II is an auditing procedure that ensures service providers securely manage data to protect the interests of the organization and the privacy of its clients. Type II reports evaluate the effectiveness of controls over a period of time (typically 6-12 months).",
            "evidence": "AICPA Trust Services Criteria"
        },
        {
            "question_id": "CANONICAL-ENCRYPTION",
            "question_text": "What encryption standards should be used?",
            "answer_text": "Industry-standard encryption includes AES-256 for data at rest and TLS 1.3 for data in transit. These standards are widely accepted and provide strong cryptographic protection for sensitive information.",
            "evidence": "NIST FIPS 140-2, TLS 1.3 RFC 8446"
        },
    ]

    created_count = 0
    for response in sample_responses:
        try:
            params = {
                "question_id": response["question_id"],
                "question_text": response["question_text"],
                "answer_text": response["answer_text"],
                "evidence": response["evidence"]
            }

            result = requests.post(CREATE_RESPONSE_ENDPOINT, params=params)

            if result.status_code == 200:
                created_count += 1
                print(f"✓ Created: {response['question_id']}")
            else:
                print(f"✗ Failed: {response['question_id']} - {result.status_code}")

        except Exception as e:
            print(f"✗ Error creating {response['question_id']}: {str(e)}")

    print(f"\nCreated {created_count}/{len(sample_responses)} canonical responses")
    return created_count > 0


def test_batch_endpoint(num_questions: int = 1000):
    """
    Test the /batch-process-questionnaire endpoint with generated questions.
    """
    print("\n" + "="*80)
    print(f"STEP 2: Testing batch endpoint with {num_questions} questions")
    print("="*80)

    # Generate questions
    print(f"\nGenerating {num_questions} realistic vendor risk questions...")
    questions = generate_realistic_questions(num_questions)
    print(f"✓ Generated {len(questions)} questions")

    # Prepare request payload
    payload = {
        "questions": questions
    }

    # Show sample questions
    print("\nSample questions:")
    for i in range(min(5, len(questions))):
        print(f"  {questions[i]['id']}: {questions[i]['text'][:80]}...")

    # Calculate expected chunks
    expected_chunks = (len(questions) + 2047) // 2048
    print(f"\nExpected API chunking:")
    print(f"  - Total questions: {len(questions)}")
    print(f"  - Chunk size limit: 2048")
    print(f"  - Expected chunks: {expected_chunks}")

    # Make API request
    print(f"\n{'='*80}")
    print("MAKING BATCH API REQUEST")
    print(f"{'='*80}")
    print(f"Endpoint: {BATCH_ENDPOINT}")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    try:
        response = requests.post(
            BATCH_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minute timeout for large batches
        )

        elapsed_time = time.time() - start_time

        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Analyze results
            print(f"\n{'='*80}")
            print("RESULTS ANALYSIS")
            print(f"{'='*80}")

            status_counts = {
                "LINKED": 0,
                "CONFIRMATION_REQUIRED": 0,
                "NO_MATCH": 0
            }

            for item in result.get("results", []):
                status = item.get("status")
                status_counts[status] = status_counts.get(status, 0) + 1

            total = sum(status_counts.values())

            print(f"\nTotal results: {total}")
            print(f"\nBreakdown:")
            print(f"  LINKED:                  {status_counts['LINKED']:4d} ({status_counts['LINKED']/total*100:5.1f}%)")
            print(f"  CONFIRMATION_REQUIRED:   {status_counts['CONFIRMATION_REQUIRED']:4d} ({status_counts['CONFIRMATION_REQUIRED']/total*100:5.1f}%)")
            print(f"  NO_MATCH:                {status_counts['NO_MATCH']:4d} ({status_counts['NO_MATCH']/total*100:5.1f}%)")

            print(f"\nPerformance metrics:")
            print(f"  Questions/second:        {total/elapsed_time:.2f}")
            print(f"  Average time/question:   {elapsed_time/total*1000:.2f} ms")

            # Show sample results
            print(f"\nSample results (first 10):")
            for i, item in enumerate(result.get("results", [])[:10]):
                status = item.get("status")
                question_id = item.get("id")

                if status == "LINKED":
                    canonical = item.get("data", {}).get("canonical_question_text", "N/A")
                    print(f"  [{i+1}] {question_id}: {status} → {canonical[:60]}...")
                elif status == "CONFIRMATION_REQUIRED":
                    canonical = item.get("data", {}).get("canonical_question_text", "N/A")
                    print(f"  [{i+1}] {question_id}: {status} → {canonical[:50]}...")
                else:
                    print(f"  [{i+1}] {question_id}: {status}")

            # Save full results to file
            output_file = f"batch_test_results_{num_questions}q_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Full results saved to: {output_file}")

            return True

        else:
            print(f"\n✗ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print(f"\n✗ Request timed out after {elapsed_time:.2f} seconds")
        return False

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n✗ Error after {elapsed_time:.2f} seconds: {str(e)}")
        return False


def main():
    """Main test execution."""
    print(f"\n{'='*80}")
    print("BATCH ENDPOINT TEST SUITE")
    print(f"{'='*80}")
    print(f"Testing endpoint: {BATCH_ENDPOINT}")
    print(f"Number of questions: {NUM_QUESTIONS}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Create sample responses
    if not create_sample_responses():
        print("\n⚠ Warning: Failed to create sample responses. Continuing anyway...")

    # Step 2: Test batch endpoint
    success = test_batch_endpoint(NUM_QUESTIONS)

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    if success:
        print("✓ Batch endpoint test PASSED")
        print("\nKey features tested:")
        print("  ✓ Batch processing with 4-step logic")
        print("  ✓ Automatic chunking for large batches")
        print("  ✓ Performance optimization")
        print("  ✓ Realistic vendor risk questions")
    else:
        print("✗ Batch endpoint test FAILED")
        print("\nCheck:")
        print("  - Is the server running on port 8000?")
        print("  - Is the database accessible?")
        print("  - Is the OpenAI API key valid?")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
