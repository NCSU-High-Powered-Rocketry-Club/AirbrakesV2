window.BENCHMARK_DATA = {
  "lastUpdate": 1742948321620,
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
          "id": "aee01e3ae4860422a36dbff305b57eda65c30e16",
          "message": "Adding integration back",
          "timestamp": "2025-03-18T18:39:01Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/181/commits/aee01e3ae4860422a36dbff305b57eda65c30e16"
        },
        "date": 1742945483752,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 600.074439182723,
            "unit": "iter/sec",
            "range": "stddev: 0.0006856499507863217",
            "extra": "mean: 1.6664599168095864 msec\nrounds: 577"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6394.38829657154,
            "unit": "iter/sec",
            "range": "stddev: 0.000005433552098406788",
            "extra": "mean: 156.38712471311243 usec\nrounds: 2614"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 307537.5935876242,
            "unit": "iter/sec",
            "range": "stddev: 0.000011722624718901525",
            "extra": "mean: 3.251634989837683 usec\nrounds: 13512"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 810531.8162496645,
            "unit": "iter/sec",
            "range": "stddev: 1.433945547809831e-7",
            "extra": "mean: 1.2337578611374023 usec\nrounds: 142187"
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
          "id": "5a41d29fafae31213adb191c96610e3509fe8cf1",
          "message": "Adding integration back",
          "timestamp": "2025-03-18T18:39:01Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/181/commits/5a41d29fafae31213adb191c96610e3509fe8cf1"
        },
        "date": 1742948307796,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1072.4553491044687,
            "unit": "iter/sec",
            "range": "stddev: 0.000875129529458442",
            "extra": "mean: 932.4397522330687 usec\nrounds: 448"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3030.23496521221,
            "unit": "iter/sec",
            "range": "stddev: 0.000011832281614544299",
            "extra": "mean: 330.007412454885 usec\nrounds: 1622"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 147359.85611615944,
            "unit": "iter/sec",
            "range": "stddev: 0.000018019116297697392",
            "extra": "mean: 6.786108689002312 usec\nrounds: 10093"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 491342.78402612475,
            "unit": "iter/sec",
            "range": "stddev: 4.110111335173192e-7",
            "extra": "mean: 2.0352390072891144 usec\nrounds: 88968"
          }
        ]
      }
    ]
  }
}