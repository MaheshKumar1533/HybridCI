import os

def select_tests(changed_files, dependency_graph, test_map):
    impacted_tests = set()

    # Normalize changed file names
    changed_files = [os.path.basename(f) for f in changed_files]

    for file in changed_files:
        for test, covered_files in test_map.items():
            if file in covered_files:
                impacted_tests.add(test)

    return list(impacted_tests)
