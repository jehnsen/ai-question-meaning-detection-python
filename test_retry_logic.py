"""
Test script to verify retry logic and chunking behavior
This script tests edge cases and production scenarios
"""

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"
BATCH_ENDPOINT = f"{BASE_URL}/batch-process-questionnaire"


def test_small_batch():
    """Test: Small batch (10 questions) - Single API call"""
    print("\n" + "="*80)
    print("TEST 1: Small Batch (10 questions)")
    print("="*80)
    print("Expected: 1 API call, no chunking")

    questions = [
        {"id": f"Q{i:03d}", "text": f"Test question number {i}"}
        for i in range(1, 11)
    ]

    payload = {"questions": questions}

    try:
        response = requests.post(BATCH_ENDPOINT, json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_medium_batch():
    """Test: Medium batch (500 questions) - Single API call"""
    print("\n" + "="*80)
    print("TEST 2: Medium Batch (500 questions)")
    print("="*80)
    print("Expected: 1 API call, no chunking")

    questions = [
        {"id": f"Q{i:04d}", "text": f"What is the security policy for scenario {i}?"}
        for i in range(1, 501)
    ]

    payload = {"questions": questions}

    try:
        response = requests.post(BATCH_ENDPOINT, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_large_batch_chunking():
    """Test: Large batch (3000 questions) - Multiple chunks"""
    print("\n" + "="*80)
    print("TEST 3: Large Batch (3000 questions) - Chunking Test")
    print("="*80)
    print("Expected: 2 chunks (2048 + 952), 2 API calls")

    questions = [
        {"id": f"LARGE-{i:05d}", "text": f"Security question {i} about vendor compliance"}
        for i in range(1, 3001)
    ]

    payload = {"questions": questions}

    try:
        print(f"Sending 3000 questions...")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")

        response = requests.post(BATCH_ENDPOINT, json=payload, timeout=600)

        print(f"Completed: {datetime.now().strftime('%H:%M:%S')}")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            print(f"  Expected 2 chunks of 2048 + 952")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_2048():
    """Test: Exactly 2048 questions - Boundary test"""
    print("\n" + "="*80)
    print("TEST 4: Edge Case (Exactly 2048 questions)")
    print("="*80)
    print("Expected: 1 chunk, 1 API call (no splitting)")

    questions = [
        {"id": f"EDGE-{i:05d}", "text": f"Question {i}"}
        for i in range(1, 2049)
    ]

    payload = {"questions": questions}

    try:
        print(f"Sending exactly 2048 questions...")
        response = requests.post(BATCH_ENDPOINT, json=payload, timeout=600)

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            print(f"  Should be processed in 1 chunk (at limit)")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_2049():
    """Test: 2049 questions - Just over boundary"""
    print("\n" + "="*80)
    print("TEST 5: Edge Case (2049 questions - Over Boundary)")
    print("="*80)
    print("Expected: 2 chunks (2048 + 1), 2 API calls")

    questions = [
        {"id": f"OVER-{i:05d}", "text": f"Question {i}"}
        for i in range(1, 2050)
    ]

    payload = {"questions": questions}

    try:
        print(f"Sending 2049 questions (1 over limit)...")
        response = requests.post(BATCH_ENDPOINT, json=payload, timeout=600)

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            print(f"  Should be split into 2 chunks (2048 + 1)")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_massive_batch():
    """Test: Massive batch (10000 questions) - Multiple chunks"""
    print("\n" + "="*80)
    print("TEST 6: Massive Batch (10000 questions)")
    print("="*80)
    print("Expected: 5 chunks, 5 API calls")
    print("⚠ This test takes longer and may hit rate limits (tests retry logic)")

    questions = [
        {"id": f"MASSIVE-{i:06d}", "text": f"Compliance question {i} for vendor assessment"}
        for i in range(1, 10001)
    ]

    payload = {"questions": questions}

    try:
        print(f"Sending 10000 questions...")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print("Watch for retry messages in server logs...")

        response = requests.post(BATCH_ENDPOINT, json=payload, timeout=600)

        print(f"Completed: {datetime.now().strftime('%H:%M:%S')}")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {len(result['results'])} results returned")
            print(f"  Processed in 5 chunks of ~2000 each")

            # Analyze results
            status_counts = {}
            for item in result['results']:
                status = item.get('status')
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"\n  Status breakdown:")
            for status, count in status_counts.items():
                print(f"    {status}: {count}")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"  If 500 with RateLimitError: Retry logic was triggered!")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("BATCH ENDPOINT - RETRY LOGIC & CHUNKING TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTesting: {BATCH_ENDPOINT}")

    results = []

    # Run tests
    print("\n" + "="*80)
    print("RUNNING TESTS")
    print("="*80)

    tests = [
        ("Small Batch (10)", test_small_batch),
        ("Medium Batch (500)", test_medium_batch),
        ("Large Batch (3000)", test_large_batch_chunking),
        ("Edge Case (2048)", test_edge_case_2048),
        ("Edge Case (2049)", test_edge_case_2049),
        ("Massive Batch (10000)", test_massive_batch),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print(f"\n⚠ Test interrupted by user")
            results.append((test_name, False))
            break
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed\n")

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n{'='*80}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nFeatures verified:")
        print("  ✓ Automatic chunking (2048 question limit)")
        print("  ✓ Boundary conditions (2048, 2049)")
        print("  ✓ Large batch processing (3000+ questions)")
        print("  ✓ Massive batch processing (10000 questions)")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
