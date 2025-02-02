window.BENCHMARK_DATA = {
  "lastUpdate": 1738459630559,
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
          "id": "eb77ab2606f0c59f7f5eb1b3c76b2d1722d06e79",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/eb77ab2606f0c59f7f5eb1b3c76b2d1722d06e79"
        },
        "date": 1738459613027,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1608.7799236938386,
            "unit": "iter/sec",
            "range": "stddev: 0.00042934583721102027",
            "extra": "mean: 621.5890596794311 usec\nrounds: 554"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6434.982690955376,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049306034970596685",
            "extra": "mean: 155.40057340100384 usec\nrounds: 2726"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 234245.3623030516,
            "unit": "iter/sec",
            "range": "stddev: 0.000002183842930917505",
            "extra": "mean: 4.269027954996456 usec\nrounds: 13577"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 464204.8775328276,
            "unit": "iter/sec",
            "range": "stddev: 1.5594281505474146e-7",
            "extra": "mean: 2.1542212251513493 usec\nrounds: 142369"
          }
        ]
      }
    ]
  }
}