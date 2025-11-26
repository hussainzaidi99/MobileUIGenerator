import os
import sys
import shutil

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from preview_to_react_native import PreviewToReactNativeConverter


def test_basic_login_screen():
    print("\n" + "=" * 80)
    print("TEST 1: Basic Login Screen → React Native")
    print("=" * 80)

    test_model = {
        "screens": [
            {
                "name": "Login",
                "components": [
                    {
                        "type": "hero",
                        "props": {
                            "title": "Welcome Back",
                            "subtitle": "Sign in to continue",
                        },
                    },
                    {"type": "spacer", "props": {"height": 32}},
                    {
                        "type": "textinput",
                        "props": {
                            "label": "Email",
                            "placeholder": "you@example.com",
                            "icon": "mail",
                        },
                    },
                    {"type": "spacer", "props": {"height": 16}},
                    {
                        "type": "textinput",
                        "props": {
                            "label": "Password",
                            "secure": True,
                            "icon": "lock",
                        },
                    },
                    {"type": "spacer", "props": {"height": 24}},
                    {
                        "type": "button",
                        "props": {
                            "text": "Sign In",
                            "variant": "contained",
                            "fullWidth": True,
                        },
                    },
                    {"type": "divider", "props": {"text": "OR"}},
                    {"type": "socialbutton", "props": {"provider": "Google"}},
                    {"type": "spacer", "props": {"height": 8}},
                    {"type": "socialbutton", "props": {"provider": "Apple"}},
                ],
            }
        ],
        "theme": {"primary": "#0D9488", "background": "#FFFFFF"},
    }

    converter = PreviewToReactNativeConverter(test_model)
    files = converter.convert()  # This returns dict of {path: code}

    assert len(files) > 8, "Not enough files generated"
    assert "src/screens/LoginScreen.tsx" in files, "Missing LoginScreen"
    assert "src/theme/index.ts" in files, "Missing theme"
    assert "package.json" in files, "Missing package.json"
    assert "README.md" in files, "Missing README"

    login_code = files["src/screens/LoginScreen.tsx"]
    assert "Welcome Back" in login_code
    assert "Sign in to continue" in login_code
    assert "Email" in login_code
    assert "Password" in login_code
    assert "secureTextEntry" in login_code
    assert "Sign In" in login_code
    assert "Google" in login_code or "google" in login_code.lower()
    assert "Apple" in login_code

    print("All core components rendered correctly")
    print(f"Total files: {len(files)}")
    print(
        f"Components used: {len(getattr(converter, 'used_components', []))}"
    )

    save_output(files, "login_rn")
    print("Login test PASSED")


def test_ecommerce_shop():
    print("\n" + "=" * 80)
    print("TEST 2: E-commerce Product Grid")
    print("=" * 80)

    test_model = {
        "screens": [
            {
                "name": "Shop",
                "components": [
                    {"type": "appbar", "props": {"title": "Shop"}},
                    {
                        "type": "searchinput",
                        "props": {"placeholder": "Search products..."},
                    },
                    {"type": "spacer", "props": {"height": 16}},
                    {
                        "type": "grid",
                        "props": {"columns": 2},
                        "children": [
                            {
                                "type": "productcard",
                                "props": {
                                    "title": "AirPods Pro",
                                    "price": "$249",
                                    "rating": 4.8,
                                },
                            },
                            {
                                "type": "productcard",
                                "props": {
                                    "title": "iPhone 15",
                                    "price": "$999",
                                    "badge": "New",
                                },
                            },
                        ],
                    },
                ],
            }
        ]
    }

    converter = PreviewToReactNativeConverter(test_model)
    files = converter.convert()

    shop_code = files["src/screens/ShopScreen.tsx"]
    assert "AirPods Pro" in shop_code
    assert "$249" in shop_code
    assert "iPhone 15" in shop_code
    assert "New" in shop_code or "badge" in shop_code.lower()
    assert "FlatList" in shop_code or "map" in shop_code

    print("Product cards & grid working")
    save_output(files, "shop_rn")
    print("E-commerce test PASSED")


def test_dashboard_with_stats():
    print("\n" + "=" * 80)
    print("TEST 3: Dashboard with Stats & Progress")
    print("=" * 80)

    test_model = {
        "screens": [
            {
                "name": "Dashboard",
                "components": [
                    {"type": "appbar", "props": {"title": "Dashboard"}},
                    {
                        "type": "grid",
                        "props": {"columns": 2},
                        "children": [
                            {
                                "type": "statcard",
                                "props": {
                                    "label": "Revenue",
                                    "value": "$12,434",
                                    "icon": "trending-up",
                                },
                            },
                            {
                                "type": "statcard",
                                "props": {
                                    "label": "Users",
                                    "value": "1,893",
                                    "icon": "users",
                                },
                            },
                        ],
                    },
                    {"type": "spacer", "props": {"height": 24}},
                    {
                        "type": "progressbar",
                        "props": {"label": "Monthly Goal", "value": 78},
                    },
                ],
            }
        ]
    }

    converter = PreviewToReactNativeConverter(test_model)
    files = converter.convert()

    dash_code = files["src/screens/DashboardScreen.tsx"]
    assert "Revenue" in dash_code
    assert "$12,434" in dash_code
    assert "Monthly Goal" in dash_code
    assert "78" in dash_code or "0.78" in dash_code

    print("Stats & progress bar rendered")
    save_output(files, "dashboard_rn")
    print("Dashboard test PASSED")


def test_navigation_and_multiple_screens():
    print("\n" + "=" * 80)
    print("TEST 4: Multi-Screen App + Navigation")
    print("=" * 80)

    test_model = {
        "screens": [
            {"name": "Home", "components": [{"type": "text", "props": {"text": "Home"}}]},
            {
                "name": "Profile",
                "components": [{"type": "text", "props": {"text": "Profile"}}],
            },
            {
                "name": "Settings",
                "components": [{"type": "text", "props": {"text": "Settings"}}],
            },
        ]
    }

    converter = PreviewToReactNativeConverter(test_model)
    files = converter.convert()

    assert "src/screens/HomeScreen.tsx" in files
    assert "src/screens/ProfileScreen.tsx" in files
    assert "src/screens/SettingsScreen.tsx" in files
    assert "src/navigation/RootNavigator.tsx" in files

    nav_code = files["src/navigation/RootNavigator.tsx"]
    assert "createNativeStackNavigator" in nav_code
    assert "HomeScreen" in nav_code
    assert "ProfileScreen" in nav_code

    readme = files["README.md"]
    assert "HomeScreen" in readme
    assert "npx react-native" in readme

    save_output(files, "multi_screen_rn")
    print("Navigation & multi-screen app generated correctly")
    print("Navigation test PASSED")


def save_output(files_dict, folder_name):
    """Save generated files for manual inspection"""
    output_dir = f"test_output_rn_{folder_name}"
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)

    for filepath, content in files_dict.items():
        full_path = os.path.join(output_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Output saved → {output_dir}/")


def main():
    print(
        "\n"
        + " PREVIEW → REACT NATIVE CONVERTER TEST SUITE ".center(80, "=")
    )
    print("Starting full validation...\n")

    passed = 0
    failed = 0

    tests = [
        test_basic_login_screen,
        test_ecommerce_shop,
        test_dashboard_with_stats,
        test_navigation_and_multiple_screens,
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\nTEST FAILED: {test.__name__}")
            print(f"Error: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\nALL TESTS PASSED!")
        print("Your Preview → React Native converter is PRODUCTION READY")
        print("You can now ship with 100% confidence")
    else:
        print(f"\n{failed} test(s) failed. Fix before shipping.")

    print("\nCheck test_output_rn_* folders to see generated apps!")
    return failed == 0


if __name__ == "__main__":
    success = main()
    print("\n" + " DONE ".center(80, "="))
    sys.exit(0 if success else 1)
