window.BENCHMARK_DATA = {
  "lastUpdate": 1739005301574,
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
          "id": "953e2591b2745bd1ed2358c2f63b60c2066eeed0",
          "message": "Slightly improve logging performance ",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/151/commits/953e2591b2745bd1ed2358c2f63b60c2066eeed0"
        },
        "date": 1739005286742,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1303.0875874414446,
            "unit": "iter/sec",
            "range": "stddev: 0.00036885062887222415",
            "extra": "mean: 767.4081233199804 usec\nrounds: 519"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6394.962180219791,
            "unit": "iter/sec",
            "range": "stddev: 0.000005670057090289546",
            "extra": "mean: 156.37309053884516 usec\nrounds: 2739"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 294801.26655446424,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021921792080107073",
            "extra": "mean: 3.392115684195173 usec\nrounds: 11419"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808092.5758125077,
            "unit": "iter/sec",
            "range": "stddev: 1.4783090462394058e-7",
            "extra": "mean: 1.2374819790845577 usec\nrounds: 111409"
          }
        ]
      }
    ]
  }
}