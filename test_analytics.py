"""
Test script for Analytics Dashboard endpoints
Tests all analytics endpoints with realistic data
"""

import requests
import json
from datetime import datetime
import time


BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(title)
    print("="*80)


def test_dashboard_overview():
    """Test GET /analytics/dashboard endpoint."""
    print_section("TEST 1: Dashboard Overview")

    try:
        response = requests.get(f"{BASE_URL}/analytics/dashboard")

        if response.status_code == 200:
            data = response.json()

            print("✓ Dashboard overview retrieved successfully\n")

            print("📊 TODAY'S METRICS:")
            print(f"  Questionnaires: {data['today_questionnaires']}")
            print(f"  Questions: {data['today_questions']}")
            print(f"  Linked: {data['today_linked']}")
            print(f"  Confirmation Required: {data['today_confirmation_required']}")
            print(f"  No Match: {data['today_no_match']}")

            print("\n📈 ALL-TIME TOTALS:")
            print(f"  Total Questionnaires: {data['total_questionnaires']}")
            print(f"  Total Questions: {data['total_questions']}")
            print(f"  Response Entries: {data['total_response_entries']}")
            print(f"  Question Links: {data['total_question_links']}")

            print("\n🎯 MATCH EFFECTIVENESS:")
            print(f"  Linked: {data['linked_percentage']}%")
            print(f"  Confirmation: {data['confirmation_percentage']}%")
            print(f"  No Match: {data['no_match_percentage']}%")

            print("\n⚡ PERFORMANCE:")
            if data['avg_processing_time_ms']:
                print(f"  Avg Processing Time: {data['avg_processing_time_ms']}ms")
            else:
                print(f"  Avg Processing Time: N/A (no data yet)")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_match_methods():
    """Test GET /analytics/match-methods endpoint."""
    print_section("TEST 2: Match Method Breakdown")

    try:
        response = requests.get(f"{BASE_URL}/analytics/match-methods")

        if response.status_code == 200:
            data = response.json()

            print("✓ Match method breakdown retrieved successfully\n")

            total = (data['saved_link'] + data['exact_id'] +
                    data['ai_high_confidence'] + data['ai_medium_confidence'] +
                    data['no_match'])

            print("📊 MATCH METHOD DISTRIBUTION:")
            print(f"  Saved Links:          {data['saved_link']:>6} ({data['saved_link_pct']:>5}%)")
            print(f"  Exact ID Matches:     {data['exact_id']:>6} ({data['exact_id_pct']:>5}%)")
            print(f"  AI High Confidence:   {data['ai_high_confidence']:>6} ({data['ai_high_confidence_pct']:>5}%)")
            print(f"  AI Medium Confidence: {data['ai_medium_confidence']:>6} ({data['ai_medium_confidence_pct']:>5}%)")
            print(f"  No Match:             {data['no_match']:>6} ({data['no_match_pct']:>5}%)")
            print(f"  {'─'*40}")
            print(f"  Total:                {total:>6}")

            print("\n🔍 INSIGHTS:")
            if data['saved_link_pct'] > 30:
                print("  ✓ High saved link rate - System learning well!")
            if data['no_match_pct'] > 15:
                print("  ⚠ High no-match rate - Consider adding more canonical answers")
            if data['ai_high_confidence_pct'] > 20:
                print("  ✓ AI performing well with high confidence matches")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_time_series(days=30):
    """Test GET /analytics/time-series endpoint."""
    print_section(f"TEST 3: Time-Series Data ({days} days)")

    try:
        response = requests.get(f"{BASE_URL}/analytics/time-series?days={days}")

        if response.status_code == 200:
            data = response.json()

            print(f"✓ Time-series data retrieved for {len(data['dates'])} days\n")

            # Show first 5 and last 5 days
            print("📅 DATE RANGE:")
            print(f"  From: {data['dates'][0]}")
            print(f"  To:   {data['dates'][-1]}")

            print("\n📊 SAMPLE DATA (First 5 days):")
            print(f"  {'Date':<12} {'Quest.':<8} {'Questions':<10} {'Linked':<8} {'Confirm':<8} {'No Match':<10}")
            print(f"  {'-'*70}")

            for i in range(min(5, len(data['dates']))):
                print(f"  {data['dates'][i]:<12} "
                      f"{data['questionnaires'][i]:<8} "
                      f"{data['questions'][i]:<10} "
                      f"{data['linked'][i]:<8} "
                      f"{data['confirmation_required'][i]:<8} "
                      f"{data['no_match'][i]:<10}")

            print("\n📈 AGGREGATE STATISTICS:")
            total_questions = sum(data['questions'])
            total_linked = sum(data['linked'])
            total_confirm = sum(data['confirmation_required'])
            total_no_match = sum(data['no_match'])

            print(f"  Total Questions: {total_questions}")
            print(f"  Total Linked: {total_linked} ({(total_linked/total_questions*100) if total_questions > 0 else 0:.1f}%)")
            print(f"  Total Confirmation: {total_confirm} ({(total_confirm/total_questions*100) if total_questions > 0 else 0:.1f}%)")
            print(f"  Total No Match: {total_no_match} ({(total_no_match/total_questions*100) if total_questions > 0 else 0:.1f}%)")

            # Check for trends
            if len(data['questions']) >= 7:
                first_week_avg = sum(data['questions'][:7]) / 7
                last_week_avg = sum(data['questions'][-7:]) / 7

                print("\n📊 TREND ANALYSIS:")
                if last_week_avg > first_week_avg * 1.2:
                    print(f"  📈 GROWING: +{((last_week_avg/first_week_avg - 1) * 100):.1f}% increase (first vs last week)")
                elif last_week_avg < first_week_avg * 0.8:
                    print(f"  📉 DECLINING: {((1 - last_week_avg/first_week_avg) * 100):.1f}% decrease (first vs last week)")
                else:
                    print(f"  ➡ STABLE: Usage relatively stable")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_top_questions(limit=10):
    """Test GET /analytics/top-questions endpoint."""
    print_section(f"TEST 4: Top Canonical Questions (Top {limit})")

    try:
        response = requests.get(f"{BASE_URL}/analytics/top-questions?limit={limit}")

        if response.status_code == 200:
            data = response.json()

            if data:
                print(f"✓ Retrieved {len(data)} top canonical questions\n")

                print("🏆 MOST FREQUENTLY MATCHED QUESTIONS:")
                print(f"  {'Rank':<6} {'ID':<20} {'Matches':<10} {'Avg Score':<12} {'Question':<50}")
                print(f"  {'-'*110}")

                for idx, question in enumerate(data, 1):
                    question_preview = question['question_text'][:47] + "..." if len(question['question_text']) > 50 else question['question_text']
                    avg_score = f"{question['avg_similarity_score']:.4f}" if question['avg_similarity_score'] else "N/A"

                    print(f"  #{idx:<5} {question['question_id']:<20} "
                          f"{question['match_count']:<10} "
                          f"{avg_score:<12} "
                          f"{question_preview:<50}")

                print("\n💡 INSIGHTS:")
                top_question = data[0]
                print(f"  Most popular: '{top_question['question_text'][:60]}...'")
                print(f"  Matched {top_question['match_count']} times")

                if top_question['avg_similarity_score']:
                    if top_question['avg_similarity_score'] > 0.90:
                        print(f"  ✓ High avg similarity ({top_question['avg_similarity_score']:.2f}) - Well-defined question")
                    elif top_question['avg_similarity_score'] < 0.85:
                        print(f"  ⚠ Lower avg similarity ({top_question['avg_similarity_score']:.2f}) - Consider improving answer")

            else:
                print("⚠ No top questions found (no analytics data yet)")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_vendor_insights(limit=10):
    """Test GET /analytics/vendors endpoint."""
    print_section(f"TEST 5: Vendor Insights (Top {limit})")

    try:
        response = requests.get(f"{BASE_URL}/analytics/vendors?limit={limit}")

        if response.status_code == 200:
            data = response.json()

            if data:
                print(f"✓ Retrieved {len(data)} vendor insights\n")

                print("🏢 VENDOR ANALYTICS:")
                print(f"  {'Vendor':<25} {'Quest.':<8} {'Questions':<10} {'Linked':<8} {'Confirm':<8} {'No Match':<10} {'Avg Time':<10}")
                print(f"  {'-'*100}")

                for vendor in data:
                    vendor_name = vendor['vendor_name'][:22] + "..." if len(vendor['vendor_name']) > 25 else vendor['vendor_name']
                    avg_time = f"{vendor['avg_processing_time_ms']:.1f}ms" if vendor['avg_processing_time_ms'] else "N/A"

                    print(f"  {vendor_name:<25} "
                          f"{vendor['questionnaire_count']:<8} "
                          f"{vendor['question_count']:<10} "
                          f"{vendor['linked_count']:<8} "
                          f"{vendor['confirmation_required_count']:<8} "
                          f"{vendor['no_match_count']:<10} "
                          f"{avg_time:<10}")

                print("\n💡 INSIGHTS:")
                top_vendor = data[0]
                print(f"  Most assessed: {top_vendor['vendor_name']}")
                print(f"  Questions processed: {top_vendor['question_count']}")

                # Calculate match rate
                total_questions = top_vendor['question_count']
                if total_questions > 0:
                    match_rate = (top_vendor['linked_count'] / total_questions) * 100
                    print(f"  Match rate: {match_rate:.1f}%")

                    if match_rate > 70:
                        print(f"  ✓ High match rate - Vendor with standard questions")
                    elif match_rate < 50:
                        print(f"  ⚠ Low match rate - Vendor may need special attention")

            else:
                print("⚠ No vendor data found (no analytics data with vendor context yet)")
                print("💡 TIP: Include vendor_name when calling batch endpoints")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_industry_insights():
    """Test GET /analytics/industries endpoint."""
    print_section("TEST 6: Industry Insights")

    try:
        response = requests.get(f"{BASE_URL}/analytics/industries")

        if response.status_code == 200:
            data = response.json()

            if data:
                print(f"✓ Retrieved {len(data)} industry insights\n")

                print("🏭 INDUSTRY ANALYTICS:")
                print(f"  {'Industry':<20} {'Vendors':<10} {'Quest.':<10} {'Questions':<12} {'Match %':<10}")
                print(f"  {'-'*70}")

                for industry in data:
                    industry_name = industry['industry'][:17] + "..." if len(industry['industry']) > 20 else industry['industry']

                    print(f"  {industry_name:<20} "
                          f"{industry['vendor_count']:<10} "
                          f"{industry['questionnaire_count']:<10} "
                          f"{industry['question_count']:<12} "
                          f"{industry['avg_linked_percentage']:.1f}%")

                print("\n💡 INSIGHTS:")

                # Find best and worst performing industries
                sorted_by_match = sorted(data, key=lambda x: x['avg_linked_percentage'], reverse=True)

                if len(sorted_by_match) > 0:
                    best = sorted_by_match[0]
                    print(f"  ✓ Best match rate: {best['industry']} ({best['avg_linked_percentage']:.1f}%)")

                    if len(sorted_by_match) > 1:
                        worst = sorted_by_match[-1]
                        print(f"  ⚠ Lowest match rate: {worst['industry']} ({worst['avg_linked_percentage']:.1f}%)")

                # Find most assessed industry
                sorted_by_volume = sorted(data, key=lambda x: x['question_count'], reverse=True)
                top_industry = sorted_by_volume[0]
                print(f"  📊 Most assessed: {top_industry['industry']} ({top_industry['question_count']} questions)")

            else:
                print("⚠ No industry data found (no analytics data with industry context yet)")
                print("💡 TIP: Include industry when calling batch endpoints")

            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def generate_sample_analytics_data():
    """Generate sample analytics data by processing test questionnaires."""
    print_section("SETUP: Generating Sample Analytics Data")

    print("⚠ NOTE: Analytics data is generated when using batch endpoints.")
    print("         The current implementation does NOT automatically log events.")
    print("         To see populated analytics, you need to:")
    print("         1. Process questionnaires using /batch-process-questionnaire")
    print("         2. Integrate log_analytics_event() into the endpoint")
    print("")
    print("For now, analytics endpoints will return empty/zero values.")
    print("")


def main():
    """Run all analytics tests."""
    print("\n" + "="*80)
    print("ANALYTICS DASHBOARD TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing: {BASE_URL}")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("\n✗ Server not responding. Please start the server:")
            print("  ./venv/Scripts/python main.py")
            return
    except Exception as e:
        print(f"\n✗ Cannot connect to server: {str(e)}")
        print("  Please start the server:")
        print("  ./venv/Scripts/python main.py")
        return

    # Note about sample data
    generate_sample_analytics_data()

    # Run tests
    results = []

    tests = [
        ("Dashboard Overview", test_dashboard_overview),
        ("Match Method Breakdown", test_match_methods),
        ("Time-Series Data", lambda: test_time_series(days=30)),
        ("Top Canonical Questions", lambda: test_top_questions(limit=10)),
        ("Vendor Insights", lambda: test_vendor_insights(limit=10)),
        ("Industry Insights", test_industry_insights),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        except KeyboardInterrupt:
            print(f"\n⚠ Test interrupted by user")
            results.append((test_name, False))
            break
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed\n")

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n{'='*80}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n🎉 All analytics endpoints working correctly!")
        print("\n💡 NEXT STEPS:")
        print("   1. Integrate log_analytics_event() into batch endpoints")
        print("   2. Process questionnaires with vendor_name and industry context")
        print("   3. Re-run this test to see populated analytics")
        print("   4. Build frontend dashboard using these endpoints")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")

    print("\n📚 For more information, see ANALYTICS_GUIDE.md")


if __name__ == "__main__":
    main()
