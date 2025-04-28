window.BENCHMARK_DATA = {
  "lastUpdate": 1745870469276,
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
          "id": "84671992e7dbc5dd7fa8678e658819b8f3c55ca4",
          "message": "Switch to Huntsville Configuration",
          "timestamp": "2025-04-20T21:33:42Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/200/commits/84671992e7dbc5dd7fa8678e658819b8f3c55ca4"
        },
        "date": 1745870456957,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6274.067488453606,
            "unit": "iter/sec",
            "range": "stddev: 0.000005944677332448012",
            "extra": "mean: 159.38623577772097 usec\nrounds: 1705"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 275187.7430552831,
            "unit": "iter/sec",
            "range": "stddev: 0.000003720352898779288",
            "extra": "mean: 3.633882777254028 usec\nrounds: 9563"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 812877.0244514142,
            "unit": "iter/sec",
            "range": "stddev: 1.9142148608121624e-7",
            "extra": "mean: 1.2301983816984732 usec\nrounds: 61790"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 531.2621637826282,
            "unit": "iter/sec",
            "range": "stddev: 0.00045232325259157816",
            "extra": "mean: 1.8823098428089093 msec\nrounds: 598"
          }
        ]
      }
    ]
  }
}