window.BENCHMARK_DATA = {
  "lastUpdate": 1741135927395,
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
          "id": "18579eb9c5fe4592da57f70a8ab9e5ab661f05b7",
          "message": "Use `os.fsync()` to guarantee disk write",
          "timestamp": "2025-03-04T22:10:08Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/172/commits/18579eb9c5fe4592da57f70a8ab9e5ab661f05b7"
        },
        "date": 1741135912668,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1065.944235042966,
            "unit": "iter/sec",
            "range": "stddev: 0.0008827133739080237",
            "extra": "mean: 938.1353799992098 usec\nrounds: 400"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3211.397294962684,
            "unit": "iter/sec",
            "range": "stddev: 0.000032116375504689716",
            "extra": "mean: 311.3909330273693 usec\nrounds: 1747"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 124686.55105323638,
            "unit": "iter/sec",
            "range": "stddev: 0.000006350075440951789",
            "extra": "mean: 8.020111163176198 usec\nrounds: 6315"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 505262.09986739344,
            "unit": "iter/sec",
            "range": "stddev: 3.742296049792262e-7",
            "extra": "mean: 1.9791708110749866 usec\nrounds: 49505"
          }
        ]
      }
    ]
  }
}