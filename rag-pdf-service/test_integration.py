#!/usr/bin/env python3
"""
Comprehensive test script to identify and fix application errors.
Tests LLM calls, vector store retrieval, and document processing.
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_health_endpoint():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/rag/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_llm_call():
    """Test LLM call with simple question."""
    print("\n🤖 Testing LLM call...")
    
    # Test simple question
    test_data = {
        "question": "What is the capital of France?",
        "evaluate": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/rag/ask",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ LLM call successful")
            print(f"📝 Response: {result.get('answer', 'No answer provided')[:200]}...")
            
            # Check if response contains relevant information
            if "answer" in result and len(result["answer"]) > 10:
                print("✅ LLM provided meaningful response")
                return True
            else:
                print("⚠️ LLM response seems empty or too short")
                return False
        else:
            print(f"❌ LLM call failed: {response.status_code}")
            print(f"📄 Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ LLM call error: {e}")
        return False

def test_vector_store():
    """Test vector store functionality."""
    print("\n🗄️ Testing vector store...")
    
    try:
        # Test similarity search
        test_data = {
            "question": "Tell me about France",
            "k": 3,
            "evaluate": False
        }
        
        response = requests.post(
            "http://localhost:8000/rag/ask",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Vector store query successful")
            
            # Check if sources are returned
            if "sources" in result and len(result["sources"]) > 0:
                print("✅ Vector store returned relevant documents")
                return True
            else:
                print("⚠️ No sources returned from vector store")
                return False
        else:
            print(f"❌ Vector store query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Vector store error: {e}")
        return False

def test_document_upload():
    """Test document upload functionality."""
    print("\n📄 Testing document upload...")
    
    # Create a simple test file
    test_content = """
    France is a country located in Western Europe. It is known for its rich culture, cuisine, fashion, and landmarks.
    The capital of France is Paris.
    France is famous for the Eiffel Tower, Louvre Museum, and French wine regions.
    """
    
    try:
        files = {'file': ('test_document.txt', test_content, 'text/plain')}
        response = requests.post(
            "http://localhost:8000/ingest/pdf",
            files=files,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document upload successful")
            print(f"📊 Upload result: {result}")
            return True
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            print(f"📄 Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Document upload error: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary."""
    print("🧪 Starting comprehensive integration tests...\n")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("LLM Call", test_llm_call),
        ("Vector Store", test_vector_store),
        ("Document Upload", test_document_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    print("🚀 PDF RAG Application Integration Test")
    print("=" * 50)
    
    success = run_all_tests()
    
    print(f"\n{'='*50}")
    if success:
        print("✅ Application is working correctly!")
        sys.exit(0)
    else:
        print("❌ Application has issues that need fixing!")
        sys.exit(1)
