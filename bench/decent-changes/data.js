window.BENCHMARK_DATA = {
  "lastUpdate": 1740952653433,
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
          "id": "4996d6296d98c2385243d7678dcbd949598ce86f",
          "message": "Decent changes",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/167/commits/4996d6296d98c2385243d7678dcbd949598ce86f"
        },
        "date": 1740952638102,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1079.1395256884646,
            "unit": "iter/sec",
            "range": "stddev: 0.0008434986827884556",
            "extra": "mean: 926.6642321918703 usec\nrounds: 435"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3052.256615311813,
            "unit": "iter/sec",
            "range": "stddev: 0.000012118901702624388",
            "extra": "mean: 327.6264502084932 usec\nrounds: 1657"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 125159.42856462992,
            "unit": "iter/sec",
            "range": "stddev: 0.000004982902657067204",
            "extra": "mean: 7.989809569029945 usec\nrounds: 7189"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 492528.86964418,
            "unit": "iter/sec",
            "range": "stddev: 3.561488549811646e-7",
            "extra": "mean: 2.0303378372976084 usec\nrounds: 61426"
          }
        ]
      }
    ]
  }
}