import time
import subprocess
import json
import os

# Simulate CLI behavior
def simulate_execution(modified_files, total_tests, selected_tests):
    # Baseline
    # docker build = 4.5
    # test execution = min(total_tests * 0.3, 2.0)
    baseline_time = 4.5 + min(total_tests * 0.3, 2.0)

    # Optimized
    build_time = 0
    if any(f.endswith('.js') for f in modified_files): build_time += 1.2
    if any(f.endswith('.py') for f in modified_files): build_time += 0.8
    if any(f.endswith('.java') for f in modified_files): build_time += 2.5

    # docker build cache hit = 0.5
    # test execution = min(selected_tests * 0.3, 2.0)
    optimized_time = build_time + 0.5 + min(selected_tests * 0.3, 2.0)

    return baseline_time, optimized_time

scenarios = [
    (["src/main.py"], 100, 5),
    (["src/main.py"], 100, 50),
    (["src/main.java"], 100, 5),
    (["src/main.java", "src/utils.py"], 100, 5),
    (["src/main.java", "src/utils.py", "src/app.js"], 100, 5),
    (["src/main.java", "src/utils.py", "src/app.js"], 10, 5),
]

print("Simulated Breakeven Analysis:")
for files, tot, sel in scenarios:
    b, o = simulate_execution(files, tot, sel)
    print(f"Mods: {files}, Total: {tot}, Selected: {sel}")
    print(f"  Baseline: {b:.2f}s | Optimized: {o:.2f}s")
    if o > b:
        print("  -> OPTIMIZED > BASELINE (Breakeven Exceeded!)")
    print("-" * 40)
