window.BENCHMARK_DATA = {
  "lastUpdate": 1742170733387,
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
          "id": "a64ba81b7796d817ad0aba934a5732a8ff8eef68",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/a64ba81b7796d817ad0aba934a5732a8ff8eef68"
        },
        "date": 1742170719185,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1087.3428509437374,
            "unit": "iter/sec",
            "range": "stddev: 0.0008648683332602033",
            "extra": "mean: 919.6731271393104 usec\nrounds: 409"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 2961.3457813150367,
            "unit": "iter/sec",
            "range": "stddev: 0.000026486395071682658",
            "extra": "mean: 337.6843076920024 usec\nrounds: 1534"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 123182.57204639073,
            "unit": "iter/sec",
            "range": "stddev: 0.000006376706392266044",
            "extra": "mean: 8.118031498996453 usec\nrounds: 7397"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 467179.36067953275,
            "unit": "iter/sec",
            "range": "stddev: 3.8756509421489e-7",
            "extra": "mean: 2.140505519219549 usec\nrounds: 48829"
          }
        ]
      }
    ]
  }
}