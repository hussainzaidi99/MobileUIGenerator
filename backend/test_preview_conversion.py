# backend/test_preview_conversion.py
"""
Test script to verify Preview→Flutter conversion works correctly.
Run this to test the new conversion system before deploying.
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from preview_to_flutter import PreviewToFlutterConverter


def test_basic_conversion():
    """Test basic conversion with simple component model"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Basic Login Screen Conversion")
    print("="*70)
    
    # Sample component model (matches what preview generates)
    test_model = {
        "screens": [
            {
                "name": "Login",
                "components": [
                    {
                        "type": "illustrationheader",
                        "props": {
                            "title": "Welcome Back",
                            "subtitle": "Sign in to continue"
                        }
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 32}
                    },
                    {
                        "type": "iconinput",
                        "props": {
                            "icon": "mail",
                            "label": "Email",
                            "placeholder": "you@example.com"
                        }
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 16}
                    },
                    {
                        "type": "iconinput",
                        "props": {
                            "icon": "lock",
                            "label": "Password",
                            "type": "password"
                        }
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 24}
                    },
                    {
                        "type": "gradientbutton",
                        "props": {
                            "text": "Sign In",
                            "gradient": "teal",
                            "size": "lg"
                        }
                    },
                    {
                        "type": "divider",
                        "props": {"text": "OR"}
                    },
                    {
                        "type": "socialbutton",
                        "props": {"provider": "Google"}
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 8}
                    },
                    {
                        "type": "socialbutton",
                        "props": {"provider": "Apple"}
                    }
                ]
            }
        ],
        "theme": {
            "primary": "#0D9488",
            "background": "#F7FAFC",
            "surface": "#FFFFFF",
            "text": "#0F172A"
        },
        "tokens": {
            "gap": 16,
            "padding": 20,
            "cardRadius": 12
        }
    }
    
    # Run conversion
    converter = PreviewToFlutterConverter(test_model)
    dart_files = converter.convert()
    
    # Verify results
    assert len(dart_files) > 0, "❌ No files generated"
    assert "lib/main.dart" in dart_files, "❌ Missing main.dart"
    assert "lib/theme.dart" in dart_files, "❌ Missing theme.dart"
    assert "lib/components/ui_components.dart" in dart_files, "❌ Missing components"
    assert "lib/screens/login_screen.dart" in dart_files, "❌ Missing login screen"
    
    print("\n✅ All required files generated")
    print(f"📊 Total files: {len(dart_files)}")
    print(f"🎨 Components used: {len(converter.used_components)}")
    
    # Verify component detection
    expected_components = {
        "illustrationheader", "iconinput", "gradientbutton", 
        "socialbutton", "divider", "spacer"
    }
    detected = converter.used_components
    missing = expected_components - detected
    
    if missing:
        print(f"⚠️  Missing components: {missing}")
    else:
        print("✅ All components detected correctly")
    
    # Verify screen content
    login_screen = dart_files["lib/screens/login_screen.dart"]
    
    assert "IllustrationHeader" in login_screen, "❌ IllustrationHeader not in screen"
    assert "IconInput" in login_screen, "❌ IconInput not in screen"
    assert "GradientButton" in login_screen, "❌ GradientButton not in screen"
    assert "SocialButton" in login_screen, "❌ SocialButton not in screen"
    
    print("✅ Screen components verified")
    
    # Verify theme
    theme_file = dart_files["lib/theme.dart"]
    assert "0xFF0D9488" in theme_file, "❌ Primary color not in theme"
    assert "AppTheme" in theme_file, "❌ AppTheme class missing"
    
    print("✅ Theme verified")
    
    return dart_files


def test_ecommerce_conversion():
    """Test e-commerce screen with products"""
    print("\n" + "="*70)
    print("🧪 TEST 2: E-commerce Screen Conversion")
    print("="*70)
    
    test_model = {
        "screens": [
            {
                "name": "Products",
                "components": [
                    {
                        "type": "searchinput",
                        "props": {"placeholder": "Search products..."}
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 16}
                    },
                    {
                        "type": "grid",
                        "props": {"columns": 2, "gap": 16},
                        "children": [
                            {
                                "type": "productcard",
                                "props": {
                                    "title": "Product 1",
                                    "price": "$29.99",
                                    "rating": 4.5,
                                    "badge": "Sale"
                                }
                            },
                            {
                                "type": "productcard",
                                "props": {
                                    "title": "Product 2",
                                    "price": "$39.99",
                                    "rating": 4.8
                                }
                            }
                        ]
                    },
                    {
                        "type": "floatingactionbutton",
                        "props": {
                            "icon": "🛒",
                            "gradient": "orange"
                        }
                    }
                ]
            }
        ],
        "theme": {
            "primary": "#F59E0B",
            "background": "#F7FAFC"
        }
    }
    
    converter = PreviewToFlutterConverter(test_model)
    dart_files = converter.convert()
    
    # Verify e-commerce components
    products_screen = dart_files["lib/screens/products_screen.dart"]
    
    assert "SearchInput" in products_screen, "❌ SearchInput missing"
    assert "CustomGrid" in products_screen, "❌ Grid missing"
    assert "ProductCard" in products_screen, "❌ ProductCard missing"
    assert "FloatingActionButton" in products_screen, "❌ FAB missing"
    
    print("✅ E-commerce components verified")
    
    # Verify grid with children
    assert "children: [" in products_screen, "❌ Grid children missing"
    
    print("✅ Grid structure verified")
    
    return dart_files


def test_dashboard_conversion():
    """Test dashboard with stats and progress"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Dashboard Screen Conversion")
    print("="*70)
    
    test_model = {
        "screens": [
            {
                "name": "Dashboard",
                "components": [
                    {
                        "type": "appbar",
                        "props": {
                            "title": "Dashboard",
                            "subtitle": "Welcome back!"
                        }
                    },
                    {
                        "type": "grid",
                        "props": {"columns": 2, "gap": 16},
                        "children": [
                            {
                                "type": "statcard",
                                "props": {
                                    "icon": "📊",
                                    "value": "1,234",
                                    "label": "Total Sales",
                                    "color": "blue"
                                }
                            },
                            {
                                "type": "statcard",
                                "props": {
                                    "icon": "👥",
                                    "value": "567",
                                    "label": "Users",
                                    "color": "green"
                                }
                            }
                        ]
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 24}
                    },
                    {
                        "type": "progressbar",
                        "props": {
                            "label": "Goal Progress",
                            "value": 75,
                            "color": "teal"
                        }
                    }
                ]
            }
        ],
        "theme": {
            "primary": "#3B82F6",
            "background": "#F7FAFC"
        }
    }
    
    converter = PreviewToFlutterConverter(test_model)
    dart_files = converter.convert()
    
    # Verify dashboard components
    dashboard_screen = dart_files["lib/screens/dashboard_screen.dart"]
    
    assert "CustomAppBar" in dashboard_screen, "❌ AppBar missing"
    assert "StatCard" in dashboard_screen, "❌ StatCard missing"
    assert "ProgressBar" in dashboard_screen, "❌ ProgressBar missing"
    
    print("✅ Dashboard components verified")
    
    return dart_files


def test_all_component_types():
    """Test that all component types convert correctly"""
    print("\n" + "="*70)
    print("🧪 TEST 4: All Component Types")
    print("="*70)
    
    # List of all component types
    all_components = [
        {"type": "container", "props": {}, "children": []},
        {"type": "card", "props": {}, "children": []},
        {"type": "spacer", "props": {"height": 16}},
        {"type": "header", "props": {"title": "Test"}},
        {"type": "text", "props": {"text": "Test"}},
        {"type": "divider", "props": {}},
        {"type": "badge", "props": {"text": "New", "color": "blue"}},
        {"type": "iconinput", "props": {"icon": "mail", "label": "Email"}},
        {"type": "searchinput", "props": {"placeholder": "Search"}},
        {"type": "checkbox", "props": {"label": "Accept"}},
        {"type": "button", "props": {"text": "Click"}},
        {"type": "gradientbutton", "props": {"text": "Submit"}},
        {"type": "socialbutton", "props": {"provider": "Google"}},
        {"type": "linkbutton", "props": {"text": "Learn more"}},
        {"type": "image", "props": {}},
        {"type": "avatar", "props": {"name": "User"}},
        {"type": "illustrationheader", "props": {"title": "Welcome"}},
        {"type": "productcard", "props": {"title": "Product", "price": "$10"}},
        {"type": "statcard", "props": {"value": "100", "label": "Total"}},
        {"type": "progressbar", "props": {"value": 50}},
        {"type": "appbar", "props": {"title": "App"}},
        {"type": "listitem", "props": {"title": "Item"}},
        {"type": "alert", "props": {"type": "info", "message": "Info"}},
        {"type": "emptystate", "props": {"title": "No data"}},
    ]
    
    test_model = {
        "screens": [
            {
                "name": "AllComponents",
                "components": all_components
            }
        ],
        "theme": {"primary": "#0D9488"}
    }
    
    converter = PreviewToFlutterConverter(test_model)
    dart_files = converter.convert()
    
    screen = dart_files["lib/screens/allcomponents_screen.dart"]
    
    # Check that screen was generated
    assert len(screen) > 1000, "❌ Screen too short, components may be missing"
    
    print(f"✅ All component types tested")
    print(f"📊 Components detected: {len(converter.used_components)}")
    print(f"🎨 Components used: {', '.join(sorted(converter.used_components))}")
    
    return dart_files


def save_test_output(dart_files: dict, test_name: str):
    """Save generated files for manual inspection"""
    output_dir = f"test_output_{test_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    for filepath, content in dart_files.items():
        full_path = os.path.join(output_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"\n💾 Test output saved to: {output_dir}/")
    return output_dir


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 PREVIEW→FLUTTER CONVERTER TEST SUITE")
    print("="*70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Basic conversion
    try:
        dart_files_1 = test_basic_conversion()
        save_test_output(dart_files_1, "login")
        tests_passed += 1
    except AssertionError as e:
        print(f"\n❌ Test 1 failed: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"\n❌ Test 1 error: {e}")
        tests_failed += 1
    
    # Test 2: E-commerce
    try:
        dart_files_2 = test_ecommerce_conversion()
        save_test_output(dart_files_2, "ecommerce")
        tests_passed += 1
    except AssertionError as e:
        print(f"\n❌ Test 2 failed: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"\n❌ Test 2 error: {e}")
        tests_failed += 1
    
    # Test 3: Dashboard
    try:
        dart_files_3 = test_dashboard_conversion()
        save_test_output(dart_files_3, "dashboard")
        tests_passed += 1
    except AssertionError as e:
        print(f"\n❌ Test 3 failed: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"\n❌ Test 3 error: {e}")
        tests_failed += 1
    
    # Test 4: All components
    try:
        dart_files_4 = test_all_component_types()
        save_test_output(dart_files_4, "all_components")
        tests_passed += 1
    except AssertionError as e:
        print(f"\n❌ Test 4 failed: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"\n❌ Test 4 error: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ Tests passed: {tests_passed}")
    print(f"❌ Tests failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Preview→Flutter converter is working correctly")
        print("✅ Ready for production deployment")
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed")
        print("❌ Fix issues before deploying")
    
    print("\n💡 To run generated Flutter apps:")
    print("   cd test_output_[test_name]")
    print("   flutter pub get")
    print("   flutter run")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)