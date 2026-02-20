"""
Test script to verify Supabase data storage and retrieval
"""
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: Check Supabase connection
print("=" * 50)
print("TEST 1: Checking Supabase Connection")
print("=" * 50)

try:
    from supabase import create_client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env")
        exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    print("✓ Supabase client created successfully")
except Exception as e:
    print(f"❌ Error connecting to Supabase: {e}")
    exit(1)

# Test 2: Check database tables
print("\n" + "=" * 50)
print("TEST 2: Checking Database Tables")
print("=" * 50)

tables_to_check = ['sessions', 'reports', 'posture_analysis', 'speech_analysis', 'transcripts']

for table in tables_to_check:
    try:
        response = supabase.table(table).select('*').limit(1).execute()
        print(f"✓ Table '{table}' exists - {len(response.data)} records")
    except Exception as e:
        print(f"❌ Table '{table}' error: {e}")

# Test 3: Check storage bucket
print("\n" + "=" * 50)
print("TEST 3: Checking Storage Bucket")
print("=" * 50)

try:
    buckets = supabase.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    
    if 'practice-data' in bucket_names:
        print("✓ 'practice-data' bucket exists")
    else:
        print("❌ 'practice-data' bucket NOT found")
        print(f"   Available buckets: {bucket_names}")
except Exception as e:
    print(f"❌ Error checking buckets: {e}")

# Test 4: Check latest report
print("\n" + "=" * 50)
print("TEST 4: Checking Latest Report")
print("=" * 50)

try:
    response = supabase.table('reports').select('*').order('created_at', desc=True).limit(1).execute()
    
    if response.data:
        report = response.data[0]
        print(f"✓ Latest report found")
        print(f"  - Session ID: {report.get('session_id')}")
        print(f"  - Created at: {report.get('created_at')}")
        print(f"  - Report data keys: {list(report.get('report_data', {}).keys()) if isinstance(report.get('report_data'), dict) else 'Not a dict'}")
        print(f"  - AI Feedback keys: {list(report.get('ai_feedback', {}).keys()) if isinstance(report.get('ai_feedback'), dict) else 'Not a dict'}")
    else:
        print("❌ No reports found in database - complete a practice session first")
except Exception as e:
    print(f"❌ Error retrieving report: {e}")

# Test 5: Test data structure
print("\n" + "=" * 50)
print("TEST 5: Data Structure Verification")
print("=" * 50)

try:
    response = supabase.table('reports').select('*').limit(1).execute()
    
    if response.data:
        report = response.data[0]
        
        # Check report_data
        report_data = report.get('report_data')
        if isinstance(report_data, dict):
            required_keys = ['session_id', 'timestamp', 'topic', 'posture_analysis', 'speech_analysis', 'transcript', 'overall_score']
            missing_keys = [k for k in required_keys if k not in report_data]
            
            if missing_keys:
                print(f"⚠ Report data missing keys: {missing_keys}")
            else:
                print("✓ Report data has all required keys")
        else:
            print(f"❌ report_data is not a dict: {type(report_data)}")
        
        # Check ai_feedback
        ai_feedback = report.get('ai_feedback')
        if isinstance(ai_feedback, dict):
            print(f"✓ AI feedback is valid - keys: {list(ai_feedback.keys())[:5]}...")
        else:
            print(f"❌ AI feedback is not a dict: {type(ai_feedback)}")
            
    else:
        print("⚠ No data to verify - run a practice session first")
except Exception as e:
    print(f"❌ Error verifying data: {e}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
