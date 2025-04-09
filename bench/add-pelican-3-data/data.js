window.BENCHMARK_DATA = {
  "lastUpdate": 1744164900255,
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
          "id": "63a1eb8b78637704288d84141f4192a6e14c955b",
          "message": "Add pelicanator launch 3 metadata",
          "timestamp": "2025-04-09T00:49:09Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/192/commits/63a1eb8b78637704288d84141f4192a6e14c955b"
        },
        "date": 1744164887238,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6409.361986143009,
            "unit": "iter/sec",
            "range": "stddev: 0.000003812032165269515",
            "extra": "mean: 156.02176974275946 usec\nrounds: 1798"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 277923.97499065177,
            "unit": "iter/sec",
            "range": "stddev: 0.000003408296025781884",
            "extra": "mean: 3.5981062808044393 usec\nrounds: 9870"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 803052.1354806586,
            "unit": "iter/sec",
            "range": "stddev: 1.0101558938913748e-7",
            "extra": "mean: 1.2452491635570588 usec\nrounds: 115956"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 643.1865521485244,
            "unit": "iter/sec",
            "range": "stddev: 0.0008120675200663121",
            "extra": "mean: 1.554758874636857 msec\nrounds: 694"
          }
        ]
      }
    ]
  }
}