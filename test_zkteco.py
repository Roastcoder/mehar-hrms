#!/usr/bin/env python3
"""
ZKTeco Integration Test Script
Usage: python test_zkteco.py
"""

import requests
from datetime import datetime

# Configuration
SERVER_URL = "http://hrms.meharadvisory.cloud/attendance/iclock/cdata"
DEVICE_SN = "K40PRO001"

def test_single_entry():
    """Test single attendance entry"""
    print("Testing single attendance entry...")
    
    data = "ATTLOG\t1\t2024-01-15 09:30:00\t0\t0\t0\t0"
    
    response = requests.post(
        f"{SERVER_URL}?SN={DEVICE_SN}",
        data=data,
        headers={"Content-Type": "text/plain"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_multiple_entries():
    """Test multiple attendance entries"""
    print("Testing multiple attendance entries...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = f"""ATTLOG\t1\t{now}\t0\t0\t0\t0
ATTLOG\t2\t{now}\t0\t0\t0\t0
ATTLOG\t3\t{now}\t0\t0\t0\t0"""
    
    response = requests.post(
        f"{SERVER_URL}?SN={DEVICE_SN}",
        data=data,
        headers={"Content-Type": "text/plain"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_current_time():
    """Test with current timestamp"""
    print("Testing with current timestamp...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = f"ATTLOG\t1\t{now}\t0\t1\t0\t0"
    
    response = requests.post(
        f"{SERVER_URL}?SN={DEVICE_SN}",
        data=data,
        headers={"Content-Type": "text/plain"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Timestamp sent: {now}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("ZKTeco Integration Test")
    print("=" * 50)
    print()
    
    try:
        test_single_entry()
        test_multiple_entries()
        test_current_time()
        
        print("=" * 50)
        print("All tests completed!")
        print("Check Django logs for processing details")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server")
        print(f"URL: {SERVER_URL}")
        print("Check if server is running and accessible")
    except Exception as e:
        print(f"ERROR: {str(e)}")
