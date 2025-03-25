window.BENCHMARK_DATA = {
  "lastUpdate": 1742945497131,
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
      }
    ]
  }
}