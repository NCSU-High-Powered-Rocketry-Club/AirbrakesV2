window.BENCHMARK_DATA = {
  "lastUpdate": 1740345867735,
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
          "id": "51a98251cdd1c6439b7249e8810b853dd9224fcb",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/51a98251cdd1c6439b7249e8810b853dd9224fcb"
        },
        "date": 1740345851636,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 984.8632822099753,
            "unit": "iter/sec",
            "range": "stddev: 0.000864534862962819",
            "extra": "mean: 1.015369359446581 msec\nrounds: 434"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3106.5294135173185,
            "unit": "iter/sec",
            "range": "stddev: 0.00001783503328814815",
            "extra": "mean: 321.9026337393554 usec\nrounds: 1559"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 131503.0343418168,
            "unit": "iter/sec",
            "range": "stddev: 0.000004423099756546365",
            "extra": "mean: 7.604387267602456 usec\nrounds: 6990"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503455.00051847094,
            "unit": "iter/sec",
            "range": "stddev: 3.7311162671948827e-7",
            "extra": "mean: 1.986274838804211 usec\nrounds: 62815"
          }
        ]
      }
    ]
  }
}