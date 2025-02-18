window.BENCHMARK_DATA = {
  "lastUpdate": 1739916742490,
  "repoUrl": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "130889585+wlsanderson@users.noreply.github.com",
            "name": "Will Sanderson",
            "username": "wlsanderson"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "46ad558e6d9afbb0f72ae273fe2aa20d651ed33d",
          "message": "Merge pull request #146 from NCSU-High-Powered-Rocketry-Club/imu-fix\n\nOptimize Reading IMU Data",
          "timestamp": "2025-02-18T17:10:51-05:00",
          "tree_id": "e031cf87f5b5abe3802e76f925143dd4bf058c03",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/46ad558e6d9afbb0f72ae273fe2aa20d651ed33d"
        },
        "date": 1739916726405,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1634.5392849932116,
            "unit": "iter/sec",
            "range": "stddev: 0.0003956507260947544",
            "extra": "mean: 611.7931879527466 usec\nrounds: 415"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3154.4962838987026,
            "unit": "iter/sec",
            "range": "stddev: 0.000023510434323909205",
            "extra": "mean: 317.0078231203622 usec\nrounds: 1436"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 131091.84222668316,
            "unit": "iter/sec",
            "range": "stddev: 0.000002860995215098576",
            "extra": "mean: 7.628239736465114 usec\nrounds: 6674"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 500906.4574477383,
            "unit": "iter/sec",
            "range": "stddev: 4.092191017985922e-7",
            "extra": "mean: 1.9963807316345774 usec\nrounds: 54348"
          }
        ]
      }
    ]
  }
}