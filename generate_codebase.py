import os

src_dir = "src"
tests_dir = "tests"

os.makedirs(src_dir, exist_ok=True)
os.makedirs(tests_dir, exist_ok=True)

modules = [
    "user_manager", "payment_gateway", "inventory_tracker", "shipping_router", 
    "notification_sender", "analytics_engine", "billing_processor", "report_generator", 
    "auth_oauth", "database_util", "cache_util", "logging_util", "security_scanner", 
    "api_gateway", "worker_node", "email_service", "sms_service", "job_queue", 
    "scheduler", "config_mgr", "invoice_builder", "tax_calculator", "order_manager", 
    "product_catalog", "discount_engine", "recommendation_ai", "search_indexer", 
    "metrics_collector", "health_checker", "audit_logger"
]

for mod in modules:
    # Create source file
    src_content = f"def init_{mod}():\n    pass\n\ndef process_{mod}():\n    return True\n"
    with open(f"{src_dir}/{mod}.py", "w") as f:
        f.write(src_content)
        
    # Create test file with sleep to simulate real workloads
    test_content = f"import pytest\nimport sys, os, time\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))\nimport {mod}\n\n"
    for i in range(15):  # 15 tests per module
        test_content += f"def test_{mod}_functionality_{i}():\n"
        test_content += f"    time.sleep(0.05)  # Simulate real database/IO wait\n"
        test_content += f"    assert {mod}.process_{mod}() == True\n\n"
        
    with open(f"{tests_dir}/test_{mod}.py", "w") as f:
        f.write(test_content)

print(f"Generated {len(modules)} modules and {len(modules)*15} test cases.")
