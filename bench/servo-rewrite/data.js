window.BENCHMARK_DATA = {
  "lastUpdate": 1743871080866,
  "repoUrl": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "name": "NCSU-High-Powered-Rocketry-Club",
            "username": "NCSU-High-Powered-Rocketry-Club"
          },
          "committer": {
            "name": "NCSU-High-Powered-Rocketry-Club",
            "username": "NCSU-High-Powered-Rocketry-Club"
          },
          "id": "488c72ad45b7b3796afc6fbe1084d4387ca158bd",
          "message": "Servo rewrite launch day",
          "timestamp": "2025-04-05T01:16:01Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/188/commits/488c72ad45b7b3796afc6fbe1084d4387ca158bd"
        },
        "date": 1743871061347,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6406.028804222354,
            "unit": "iter/sec",
            "range": "stddev: 0.000004158333021634403",
            "extra": "mean: 156.10295091724817 usec\nrounds: 1691"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 249713.19333331304,
            "unit": "iter/sec",
            "range": "stddev: 0.000004271750981117091",
            "extra": "mean: 4.00459417722962 usec\nrounds: 8038"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 807237.874991727,
            "unit": "iter/sec",
            "range": "stddev: 1.1763177786255589e-7",
            "extra": "mean: 1.2387922209550049 usec\nrounds: 110218"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 777.4665896679854,
            "unit": "iter/sec",
            "range": "stddev: 0.0009306026829333669",
            "extra": "mean: 1.2862289046106106 msec\nrounds: 629"
          }
        ]
      }
    ]
  }
}