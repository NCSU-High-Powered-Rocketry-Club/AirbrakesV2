window.BENCHMARK_DATA = {
  "lastUpdate": 1746385470582,
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
          "id": "02ea0ad00ba0f6f30d57d77764008a8c089c8071",
          "message": "Added huntsville launch data",
          "timestamp": "2025-05-04T15:35:23Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/201/commits/02ea0ad00ba0f6f30d57d77764008a8c089c8071"
        },
        "date": 1746385458323,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6230.996421456324,
            "unit": "iter/sec",
            "range": "stddev: 0.000008319344604580324",
            "extra": "mean: 160.4879753351355 usec\nrounds: 1581"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 254270.0650494385,
            "unit": "iter/sec",
            "range": "stddev: 0.000005177330577578478",
            "extra": "mean: 3.932826303424931 usec\nrounds: 8607"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 803227.4763258576,
            "unit": "iter/sec",
            "range": "stddev: 2.3568868132716822e-7",
            "extra": "mean: 1.2449773314207628 usec\nrounds: 87169"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 609.4485659832491,
            "unit": "iter/sec",
            "range": "stddev: 0.0007441974093079756",
            "extra": "mean: 1.6408275543099489 msec\nrounds: 534"
          }
        ]
      }
    ]
  }
}