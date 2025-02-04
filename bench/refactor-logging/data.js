window.BENCHMARK_DATA = {
  "lastUpdate": 1738633975516,
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
          "id": "944878d43fcf2af4ed205dbec483ab441351a8cd",
          "message": "Slightly improve logging performance ",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/151/commits/944878d43fcf2af4ed205dbec483ab441351a8cd"
        },
        "date": 1738633961877,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1623.6067376716128,
            "unit": "iter/sec",
            "range": "stddev: 0.00042890373672954885",
            "extra": "mean: 615.9126941257236 usec\nrounds: 474"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6518.359725933629,
            "unit": "iter/sec",
            "range": "stddev: 0.0000058058478737372125",
            "extra": "mean: 153.41282808026818 usec\nrounds: 2350"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 280846.07707957574,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024974033923554214",
            "extra": "mean: 3.5606692833265288 usec\nrounds: 10326"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 790491.2920597243,
            "unit": "iter/sec",
            "range": "stddev: 1.242747650208946e-7",
            "extra": "mean: 1.2650360731923744 usec\nrounds: 92585"
          }
        ]
      }
    ]
  }
}