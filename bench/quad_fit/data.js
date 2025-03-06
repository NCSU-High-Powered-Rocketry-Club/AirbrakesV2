window.BENCHMARK_DATA = {
  "lastUpdate": 1741224831868,
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
          "id": "2c6d2e51af4de06715de1e777389c0b15ef4ac2b",
          "message": "Added altitude and vel fix for when airbrakes deploy",
          "timestamp": "2025-03-06T00:57:38Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/173/commits/2c6d2e51af4de06715de1e777389c0b15ef4ac2b"
        },
        "date": 1741223992930,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1014.9275237878315,
            "unit": "iter/sec",
            "range": "stddev: 0.0008942335640712718",
            "extra": "mean: 985.2920297873878 usec\nrounds: 470"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3149.98597072447,
            "unit": "iter/sec",
            "range": "stddev: 0.000014714864913600977",
            "extra": "mean: 317.46173135177753 usec\nrounds: 1582"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 149291.0369578193,
            "unit": "iter/sec",
            "range": "stddev: 0.000020022307104295",
            "extra": "mean: 6.698325769433432 usec\nrounds: 8813"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 511438.83892376383,
            "unit": "iter/sec",
            "range": "stddev: 3.9891012193484097e-7",
            "extra": "mean: 1.955268008398287 usec\nrounds: 81434"
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
          "id": "ebd146c5827bfab25c36ad8dd5ad2b90ac582b4c",
          "message": "Added altitude and vel fix for when airbrakes deploy",
          "timestamp": "2025-03-06T00:57:38Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/173/commits/ebd146c5827bfab25c36ad8dd5ad2b90ac582b4c"
        },
        "date": 1741224817198,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 879.2389302629066,
            "unit": "iter/sec",
            "range": "stddev: 0.0008752730179574531",
            "extra": "mean: 1.137347273398124 msec\nrounds: 406"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 2985.748015256773,
            "unit": "iter/sec",
            "range": "stddev: 0.0000313414969239464",
            "extra": "mean: 334.924446031659 usec\nrounds: 1612"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 133662.4558623768,
            "unit": "iter/sec",
            "range": "stddev: 0.000005515101111430486",
            "extra": "mean: 7.481532443408286 usec\nrounds: 8168"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 473198.4950482364,
            "unit": "iter/sec",
            "range": "stddev: 3.5826280922187833e-7",
            "extra": "mean: 2.11327806504977 usec\nrounds: 71023"
          }
        ]
      }
    ]
  }
}