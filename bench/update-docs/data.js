window.BENCHMARK_DATA = {
  "lastUpdate": 1739926281453,
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
          "id": "50a1e86a135cf5e87d52eb9b7dd0dbdebb7b0bf7",
          "message": "Meticulous Refining of Comments & Docs",
          "timestamp": "2025-02-18T22:21:57Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/153/commits/50a1e86a135cf5e87d52eb9b7dd0dbdebb7b0bf7"
        },
        "date": 1739926264709,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1634.6081352679514,
            "unit": "iter/sec",
            "range": "stddev: 0.00041162828741236413",
            "extra": "mean: 611.7674190065596 usec\nrounds: 463"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3231.53481189253,
            "unit": "iter/sec",
            "range": "stddev: 0.00001188737380804287",
            "extra": "mean: 309.45048040944846 usec\nrounds: 1659"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 150251.4165973857,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033837554530659193",
            "extra": "mean: 6.6555112933118235 usec\nrounds: 8412"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 499279.60570685595,
            "unit": "iter/sec",
            "range": "stddev: 3.374500974025609e-7",
            "extra": "mean: 2.0028857349064926 usec\nrounds: 55310"
          }
        ]
      }
    ]
  }
}