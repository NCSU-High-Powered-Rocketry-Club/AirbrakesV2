window.BENCHMARK_DATA = {
  "lastUpdate": 1745870978753,
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
      },
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
          "id": "3b3f0163ee8b9d6080bc9272d43f2d0c28cf6a2d",
          "message": "Switch to Huntsville Configuration",
          "timestamp": "2025-04-20T21:33:42Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/200/commits/3b3f0163ee8b9d6080bc9272d43f2d0c28cf6a2d"
        },
        "date": 1745870966217,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6354.02913301014,
            "unit": "iter/sec",
            "range": "stddev: 0.000004211771189579462",
            "extra": "mean: 157.38045562379455 usec\nrounds: 1600"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 271492.2592068912,
            "unit": "iter/sec",
            "range": "stddev: 0.000004086272515574914",
            "extra": "mean: 3.6833462689554923 usec\nrounds: 9406"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 805404.651919532,
            "unit": "iter/sec",
            "range": "stddev: 1.7564280877016812e-7",
            "extra": "mean: 1.241611899827852 usec\nrounds: 96890"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 558.7325452937782,
            "unit": "iter/sec",
            "range": "stddev: 0.0005883625083540993",
            "extra": "mean: 1.7897650824585598 msec\nrounds: 570"
          }
        ]
      }
    ]
  }
}