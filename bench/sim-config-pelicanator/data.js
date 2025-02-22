window.BENCHMARK_DATA = {
  "lastUpdate": 1740208453006,
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
          "id": "d6873bc9740b273ff491ea8f845f3f468da11373",
          "message": "Create Simulation config for Pelicanator",
          "timestamp": "2025-02-22T05:56:08Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/157/commits/d6873bc9740b273ff491ea8f845f3f468da11373"
        },
        "date": 1740208436082,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1591.1661758126834,
            "unit": "iter/sec",
            "range": "stddev: 0.00041495671674805833",
            "extra": "mean: 628.4698702128035 usec\nrounds: 470"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3255.77760900974,
            "unit": "iter/sec",
            "range": "stddev: 0.00001222704215964409",
            "extra": "mean: 307.14628580056933 usec\nrounds: 1655"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 161407.34828904053,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033862792225329873",
            "extra": "mean: 6.195504793308716 usec\nrounds: 9388"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 513116.81607281265,
            "unit": "iter/sec",
            "range": "stddev: 3.501155921105402e-7",
            "extra": "mean: 1.9488739575007366 usec\nrounds: 65105"
          }
        ]
      }
    ]
  }
}