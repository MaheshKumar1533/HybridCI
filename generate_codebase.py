import os

src_dir = "src"
tests_dir = "tests"

os.makedirs(src_dir, exist_ok=True)
os.makedirs(tests_dir, exist_ok=True)

py_modules = [
    "user_manager", "payment_gateway", "inventory_tracker", "shipping_router", 
    "notification_sender", "analytics_engine", "billing_processor", "report_generator", 
    "auth_oauth", "database_util", "cache_util", "logging_util", "security_scanner", 
    "api_gateway", "worker_node", "email_service", "sms_service", "job_queue", 
    "scheduler", "config_mgr"
]

js_modules = [
    "dashboard_ui", "cart_component", "checkout_form", "profile_view", "product_list",
    "search_bar", "navigation_menu", "footer_links", "modal_dialog", "api_client"
]

for mod in py_modules:
    # Create source file
    src_content = f"def init_{mod}():\n    pass\n\ndef process_{mod}():\n    return True\n"
    with open(f"{src_dir}/{mod}.py", "w") as f:
        f.write(src_content)
        
    # Create test file with sleep to simulate real workloads
    test_content = f"import pytest\nimport sys, os, time\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))\nimport {mod}\n\n"
    for i in range(10):  # 10 tests per module
        test_content += f"def test_{mod}_functionality_{i}():\n"
        test_content += f"    time.sleep(0.05)  # Simulate real database/IO wait\n"
        test_content += f"    assert {mod}.process_{mod}() == True\n\n"
        
    with open(f"{tests_dir}/test_{mod}.py", "w") as f:
        f.write(test_content)

for mod in js_modules:
    # Create source file
    src_content = f"export function render_{mod}() {{\n    return '<div>{mod}</div>';\n}}\n"
    with open(f"{src_dir}/{mod}.js", "w") as f:
        f.write(src_content)
        
    # Create test file
    test_content = f"import {{ render_{mod} }} from '../src/{mod}.js';\n\n"
    for i in range(5):
        test_content += f"test('renders {mod} properly {i}', () => {{\n"
        test_content += f"    expect(render_{mod}()).toContain('{mod}');\n"
        test_content += f"}});\n\n"
        
    with open(f"{tests_dir}/test_{mod}.js", "w") as f:
        f.write(test_content)

print(f"Generated {len(py_modules)} Python modules and {len(js_modules)} JS modules.")
