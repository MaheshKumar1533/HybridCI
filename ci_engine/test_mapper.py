import os

def generate_test_map(test_dir, src_dir):
    test_map = {}

    for test_file in os.listdir(test_dir):
        if test_file.startswith("test_") and test_file.endswith(".py"):
            src_file = test_file.replace("test_", "")
            test_map[test_file] = [src_file]

    return test_map
