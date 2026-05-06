from ci_engine.pipeline_runner import run_pipeline

for i in range(10):
    result = run_pipeline(TEST_MAP, DEP_GRAPH)
    print(
        f"Run {i} | Time: {result['time']} | "
        f"Tests: {len(result['tests'])} | Cache: {result['cache_hit']}"
    )
