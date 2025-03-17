window.BENCHMARK_DATA = {
  "lastUpdate": 1742170510254,
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
          "id": "7958c3753de07992a01b98fe9789f08cf39d6b1e",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/7958c3753de07992a01b98fe9789f08cf39d6b1e"
        },
        "date": 1742170495823,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 930.9402800750868,
            "unit": "iter/sec",
            "range": "stddev: 0.000898569543012286",
            "extra": "mean: 1.0741827605948504 msec\nrounds: 472"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3243.709701897205,
            "unit": "iter/sec",
            "range": "stddev: 0.000011358269010078706",
            "extra": "mean: 308.28899374537514 usec\nrounds: 1759"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 159510.00292992996,
            "unit": "iter/sec",
            "range": "stddev: 0.00001685551715467629",
            "extra": "mean: 6.269199308079024 usec\nrounds: 10110"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 506432.7607918123,
            "unit": "iter/sec",
            "range": "stddev: 2.6980527891572e-7",
            "extra": "mean: 1.9745957951782003 usec\nrounds: 94697"
          }
        ]
      }
    ]
  }
}