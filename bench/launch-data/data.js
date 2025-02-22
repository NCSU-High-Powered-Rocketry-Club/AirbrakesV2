window.BENCHMARK_DATA = {
  "lastUpdate": 1740203743283,
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
          "id": "8c193af0977194b87bdb7c8fd0b511476a425684",
          "message": "Add legacy launch data",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/143/commits/8c193af0977194b87bdb7c8fd0b511476a425684"
        },
        "date": 1740203727390,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1625.6557070871254,
            "unit": "iter/sec",
            "range": "stddev: 0.0004076592038230684",
            "extra": "mean: 615.1364004324232 usec\nrounds: 462"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3196.870283119222,
            "unit": "iter/sec",
            "range": "stddev: 0.00003367706162151156",
            "extra": "mean: 312.80593563035933 usec\nrounds: 1740"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 132541.75113313078,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026543036154062144",
            "extra": "mean: 7.544792425411339 usec\nrounds: 6417"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 514984.4678505656,
            "unit": "iter/sec",
            "range": "stddev: 5.796944866686614e-7",
            "extra": "mean: 1.941806136743861 usec\nrounds: 54946"
          }
        ]
      }
    ]
  }
}