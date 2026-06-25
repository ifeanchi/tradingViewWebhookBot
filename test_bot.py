#!/usr/bin/env python3
"""
Test script for TradingView Webhook Bot
Tests all endpoints and functionality
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# Load env variables
from dotenv import load_dotenv
load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "test-secret")
BASE_URL = os.getenv("TEST_URL", "http://localhost:8001")

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system("pip install httpx")
    import httpx


def test_health():
    """Test /health endpoint"""
    print("\n🧪 Testing /health endpoint...")
    response = httpx.get(f"{BASE_URL}/health")
    
    if response.status_code == 200 and response.json().get("status") == "ok":
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {response.text}")
        return False


def test_webhook_valid():
    """Test valid webhook"""
    print("\n🧪 Testing valid webhook...")
    
    payload = {
        "secret": WEBHOOK_SECRET,
        "source": "Test Indicator",
        "action": "BUY",
        "symbol": "MNQ1!",
        "price": "22500.25",
        "timeframe": "15",
        "exchange": "CME_MINI",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = httpx.post(
        f"{BASE_URL}/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        print(f"✅ Valid webhook accepted: {response.json()}")
        return True
    else:
        print(f"❌ Valid webhook failed: {response.status_code} - {response.text}")
        return False


def test_webhook_invalid_secret():
    """Test invalid secret"""
    print("\n🧪 Testing invalid secret...")
    
    payload = {
        "secret": "wrong-secret",
        "source": "Test",
        "action": "BUY",
        "symbol": "TEST",
        "price": "100",
        "timeframe": "15",
        "exchange": "TEST",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = httpx.post(
        f"{BASE_URL}/webhook",
        json=payload
    )
    
    if response.status_code == 403:
        print("✅ Invalid secret rejected (403)")
        return True
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        return False


def test_webhook_missing_secret():
    """Test missing secret"""
    print("\n🧪 Testing missing secret...")
    
    payload = {
        "action": "BUY",
        "symbol": "TEST",
        "price": "100",
        "timeframe": "15",
        "exchange": "TEST",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = httpx.post(
        f"{BASE_URL}/webhook",
        json=payload
    )
    
    if response.status_code == 401:
        print("✅ Missing secret rejected (401)")
        return True
    else:
        print(f"❌ Expected 401, got {response.status_code}")
        return False


def test_webhook_invalid_action():
    """Test invalid action"""
    print("\n🧪 Testing invalid action...")
    
    payload = {
        "secret": WEBHOOK_SECRET,
        "source": "Test",
        "action": "INVALID",
        "symbol": "TEST",
        "price": "100",
        "timeframe": "15",
        "exchange": "TEST",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = httpx.post(
        f"{BASE_URL}/webhook",
        json=payload
    )
    
    if response.status_code == 400:
        print("✅ Invalid action rejected (400)")
        return True
    else:
        print(f"❌ Expected 400, got {response.status_code}")
        return False


def test_webhook_duplicate():
    """Test duplicate detection"""
    print("\n🧪 Testing duplicate detection...")
    
    payload = {
        "secret": WEBHOOK_SECRET,
        "source": "Test",
        "action": "SELL",
        "symbol": "ES1!",
        "price": "4500.00",
        "timeframe": "5",
        "exchange": "CME",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # First request
    response1 = httpx.post(f"{BASE_URL}/webhook", json=payload)
    
    # Second request (immediately - should be duplicate)
    response2 = httpx.post(f"{BASE_URL}/webhook", json=payload)
    
    if response1.status_code == 201 and response2.json().get("status") == "ignored":
        print("✅ Duplicate detected and ignored")
        return True
    else:
        print(f"❌ Duplicate detection failed")
        print(f"   First: {response1.status_code}, Second: {response2.status_code}")
        return False


def test_signals_endpoint():
    """Test /signals endpoint"""
    print("\n🧪 Testing /signals endpoint...")
    
    response = httpx.get(f"{BASE_URL}/signals")
    
    if response.status_code == 200:
        data = response.json()
        if "signals" in data and "count" in data:
            print(f"✅ Signals endpoint working ({data['count']} signals)")
            return True
    
    print(f"❌ Signals endpoint failed: {response.text}")
    return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("TradingView Webhook Bot - Test Suite")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print(f"Using secret: {WEBHOOK_SECRET[:10]}...")
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server...")
    time.sleep(1)
    
    tests = [
        ("Health Check", test_health),
        ("Valid Webhook", test_webhook_valid),
        ("Invalid Secret", test_webhook_invalid_secret),
        ("Missing Secret", test_webhook_missing_secret),
        ("Invalid Action", test_webhook_invalid_action),
        ("Duplicate Detection", test_webhook_duplicate),
        ("Signals Endpoint", test_signals_endpoint),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())