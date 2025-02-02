window.BENCHMARK_DATA = {
  "lastUpdate": 1738456242067,
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
          "id": "9bd6760480e8c199ad3fa2e07eedba1b083cbab1",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/9bd6760480e8c199ad3fa2e07eedba1b083cbab1"
        },
        "date": 1738456225278,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 479116.7162514825,
            "unit": "iter/sec",
            "range": "stddev: 1.4669664767144108e-7",
            "extra": "mean: 2.0871740978353013 usec\nrounds: 32841"
          }
        ]
      }
    ]
  }
}