window.BENCHMARK_DATA = {
  "lastUpdate": 1741023332968,
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
          "id": "3b7795a10e14b0ef237ee7a88fd1085cb47ace42",
          "message": "[pre-commit.ci] pre-commit autoupdate",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/169/commits/3b7795a10e14b0ef237ee7a88fd1085cb47ace42"
        },
        "date": 1741023317501,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1083.2794741534021,
            "unit": "iter/sec",
            "range": "stddev: 0.0008577779652407979",
            "extra": "mean: 923.122817204225 usec\nrounds: 465"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3188.9527194440716,
            "unit": "iter/sec",
            "range": "stddev: 0.000016564874833188082",
            "extra": "mean: 313.5825733328306 usec\nrounds: 1650"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 146368.72436730663,
            "unit": "iter/sec",
            "range": "stddev: 0.000004429525369781012",
            "extra": "mean: 6.832060635375484 usec\nrounds: 8312"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 502703.69703678234,
            "unit": "iter/sec",
            "range": "stddev: 4.3554272372423914e-7",
            "extra": "mean: 1.989243377151513 usec\nrounds: 34917"
          }
        ]
      }
    ]
  }
}