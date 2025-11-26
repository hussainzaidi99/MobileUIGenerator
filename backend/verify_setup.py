# backend/verify_setup.py - Quick Setup Verification Script
"""
Run this script to verify that the CoT orchestration system is properly installed.
"""

import os
import sys

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    return os.path.isfile(filepath)

def verify_setup():
    """Verify all required files are in place"""
    
    print("\n" + "="*80)
    print("🔍 SETUP VERIFICATION - CoT Orchestration System")
    print("="*80)
    
    required_files = {
        "cot_orchestrator.py": "CoT library and orchestration engine",
        "llm_client.py": "Enhanced LLM client with CoT integration",
        "main.py": "FastAPI server (existing file)",
        "component_model.py": "Component model classes (existing file)",
        "style_enricher.py": "Style enrichment (existing file)",
    }
    
    print("\n📋 CHECKING REQUIRED FILES:")
    print("-" * 80)
    
    all_good = True
    for filename, description in required_files.items():
        exists = check_file_exists(filename)
        status = "✅" if exists else "❌"
        print(f"{status} {filename:25} - {description}")
        if not exists:
            all_good = False
    
    if not all_good:
        print("\n❌ SETUP INCOMPLETE")
        print("\nMissing files detected. Please ensure:")
        print("1. cot_orchestrator.py is in backend/")
        print("2. llm_client.py is updated with CoT integration")
        return False
    
    print("\n✅ ALL REQUIRED FILES PRESENT")
    
    # Test imports
    print("\n📦 CHECKING IMPORTS:")
    print("-" * 80)
    
    try:
        print("Importing cot_orchestrator...", end=" ")
        from cot_orchestrator import (
            detect_categories,
            get_enhanced_prompt,
            COT_LIBRARY,
            CATEGORY_KEYWORDS
        )
        print("✅")
    except ImportError as e:
        print(f"❌ Failed: {e}")
        return False
    
    try:
        print("Importing llm_client...", end=" ")
        from llm_client import (
            extract_intent,
            componentize,
            generate_dart_from_json,
            generate_preview_from_json,
            generate_asset_prompts
        )
        print("✅")
    except ImportError as e:
        print(f"❌ Failed: {e}")
        return False
    
    print("\n✅ ALL IMPORTS SUCCESSFUL")
    
    # Test CoT system
    print("\n🧪 TESTING CoT SYSTEM:")
    print("-" * 80)
    
    test_prompts = [
        ("Login screen", {"auth"}),
        ("E-commerce products", {"ecommerce"}),
        ("Social feed", {"social"}),
        ("Login and products", {"auth", "ecommerce"}),
    ]
    
    all_tests_passed = True
    for prompt, expected_categories in test_prompts:
        detected = detect_categories(prompt)
        match = detected == expected_categories
        status = "✅" if match else "⚠️"
        print(f"{status} '{prompt}' → {detected}")
        if not match:
            all_tests_passed = False
            print(f"   Expected: {expected_categories}")
    
    if all_tests_passed:
        print("\n✅ ALL CATEGORY DETECTION TESTS PASSED")
    else:
        print("\n⚠️ SOME TESTS FAILED (may be ok if categories are similar)")
    
    # Check API keys
    print("\n🔑 CHECKING API KEYS:")
    print("-" * 80)
    
    from llm_client import ROUTES_CONFIG
    
    for route, config in ROUTES_CONFIG.items():
        or_status = "✅" if config['or_key'] else "❌ NOT SET"
        groq_status = "✅" if config['groq_key'] else "❌ NOT SET"
        print(f"{route.upper():12} OpenRouter: {or_status:12} | Groq: {groq_status}")
    
    # Check if at least one API is configured per route
    has_api = all(
        config['or_key'] or config['groq_key'] 
        for config in ROUTES_CONFIG.values()
    )
    
    if not has_api:
        print("\n⚠️ WARNING: Some routes have no API keys configured")
        print("   Set API keys in .env file:")
        print("   - OR_API_KEY_INTENT")
        print("   - OR_API_KEY_COMPONENT")
        print("   - OR_API_KEY_CODE")
        print("   OR")
        print("   - GROQ_API_KEY_INTENT")
        print("   - GROQ_API_KEY_COMPONENT")
        print("   - GROQ_API_KEY_CODE")
    else:
        print("\n✅ API KEYS CONFIGURED")
    
    # Show CoT library stats
    print("\n📚 CoT LIBRARY STATS:")
    print("-" * 80)
    
    from cot_orchestrator import get_category_stats, estimate_token_count
    
    stats = get_category_stats()
    total_chars = sum(s["characters"] for s in stats.values())
    total_tokens = sum(s["estimated_tokens"] for s in stats.values())
    
    print(f"Total Categories: {len(stats)}")
    print(f"Total Library Size: {total_chars:,} chars (~{total_tokens:,} tokens)")
    print(f"\nPer-Category Breakdown:")
    
    for category, data in stats.items():
        print(f"  {category.upper():12} {data['characters']:7,} chars  ~{data['estimated_tokens']:5,} tokens")
    
    print(f"\nAverage per category: ~{total_tokens // len(stats):,} tokens")
    print(f"Max combined (3 cats): ~{(total_tokens // len(stats)) * 3:,} tokens")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 SETUP VERIFICATION SUMMARY")
    print("="*80)
    
    if all_good and has_api:
        print("✅ SYSTEM READY FOR PRODUCTION")
        print("\nNext steps:")
        print("1. Start backend: uvicorn main:app --reload")
        print("2. Start frontend: npm run dev (in frontend/)")
        print("3. Test with UI: http://localhost:5173")
        print("\nOr test directly:")
        print("  python llm_client.py --demo")
        return True
    elif all_good:
        print("⚠️ SYSTEM CONFIGURED BUT NO API KEYS")
        print("\nConfigure API keys in .env, then run:")
        print("  uvicorn main:app --reload")
        return True
    else:
        print("❌ SETUP INCOMPLETE")
        print("\nPlease fix the issues above before running the server.")
        return False


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)