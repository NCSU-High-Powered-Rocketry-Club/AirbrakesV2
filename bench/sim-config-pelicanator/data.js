window.BENCHMARK_DATA = {
  "lastUpdate": 1740208478742,
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
          "id": "2240c96613405c8cbfb11a746e3f4fda4a72ea88",
          "message": "Create Simulation config for Pelicanator",
          "timestamp": "2025-02-22T05:56:08Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/157/commits/2240c96613405c8cbfb11a746e3f4fda4a72ea88"
        },
        "date": 1740208459999,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1632.4151238924248,
            "unit": "iter/sec",
            "range": "stddev: 0.0004077733333968055",
            "extra": "mean: 612.5892766881149 usec\nrounds: 459"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3150.6023160929985,
            "unit": "iter/sec",
            "range": "stddev: 0.000050240955853484166",
            "extra": "mean: 317.3996270148372 usec\nrounds: 1799"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 144627.33767978227,
            "unit": "iter/sec",
            "range": "stddev: 0.000003514081955376695",
            "extra": "mean: 6.914322119474318 usec\nrounds: 7907"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 495960.67824176024,
            "unit": "iter/sec",
            "range": "stddev: 9.831026018618666e-7",
            "extra": "mean: 2.0162888790803324 usec\nrounds: 45455"
          }
        ]
      }
    ]
  }
}