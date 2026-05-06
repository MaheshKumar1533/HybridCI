import os
import sys
import multiprocessing
import subprocess

def run_tests_in_docker(test_files):
    if not test_files:
        print("No tests to run in Docker.")
        return

    n_cores = multiprocessing.cpu_count()
    workers = max(1, n_cores - 1)
    
    print(f"Isolated Execution Layer: Detected {n_cores} CPU cores. Spawning {workers} parallel workers.")
    
    # We will build the docker image if it doesn't exist
    try:
        subprocess.check_call(["docker", "build", "-t", "hybridci-test-runner", "."])
    except Exception as e:
        print(f"Failed to build Docker image: {e}")
        print("Falling back to local execution.")
        subprocess.check_call([sys.executable, "-m", "pytest", "-n", str(workers)] + test_files)
        return

    # Run tests in docker using pytest-xdist for parallel workers
    # Mapping the local directory into the container to execute the tests
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/app",
        "-w", "/app",
        "hybridci-test-runner",
        "pytest", "-n", str(workers)
    ] + test_files
    
    try:
        subprocess.check_call(cmd)
        print("Isolated execution completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Isolated execution failed with code {e.returncode}.")
        sys.exit(e.returncode)

if __name__ == "__main__":
    tests = sys.argv[1:]
    run_tests_in_docker(tests)
