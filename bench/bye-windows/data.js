window.BENCHMARK_DATA = {
  "lastUpdate": 1739504960532,
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
          "id": "bc8fbb2530ba28adb7f9902a475de50d9a427a8c",
          "message": "Remove Windows support",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/155/commits/bc8fbb2530ba28adb7f9902a475de50d9a427a8c"
        },
        "date": 1739504946036,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1270.1307294281596,
            "unit": "iter/sec",
            "range": "stddev: 0.00035539317637893475",
            "extra": "mean: 787.320530737983 usec\nrounds: 488"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6410.882745062336,
            "unit": "iter/sec",
            "range": "stddev: 0.000006333296244137533",
            "extra": "mean: 155.98475900533361 usec\nrounds: 2332"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 281491.99184191844,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025214951440687313",
            "extra": "mean: 3.552498930632402 usec\nrounds: 10288"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 801651.5803452843,
            "unit": "iter/sec",
            "range": "stddev: 2.768359462872381e-7",
            "extra": "mean: 1.247424722308018 usec\nrounds: 87589"
          }
        ]
      }
    ]
  }
}