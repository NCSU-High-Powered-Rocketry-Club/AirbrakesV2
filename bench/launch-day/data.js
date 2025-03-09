window.BENCHMARK_DATA = {
  "lastUpdate": 1741482870989,
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
          "id": "075d5d7e00afd14b0af1f4ef9f55da0fda790c44",
          "message": "Launch config for Pelicanator Flight 2",
          "timestamp": "2025-03-08T03:10:21Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/176/commits/075d5d7e00afd14b0af1f4ef9f55da0fda790c44"
        },
        "date": 1741482857104,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 864.5436497949979,
            "unit": "iter/sec",
            "range": "stddev: 0.0008836410369626426",
            "extra": "mean: 1.1566795964982473 msec\nrounds: 456"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3033.664953134713,
            "unit": "iter/sec",
            "range": "stddev: 0.000013270666169718965",
            "extra": "mean: 329.63429233234575 usec\nrounds: 1618"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 125311.16507401815,
            "unit": "iter/sec",
            "range": "stddev: 0.000005849601477856223",
            "extra": "mean: 7.980134885900431 usec\nrounds: 7421"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 474612.6612716194,
            "unit": "iter/sec",
            "range": "stddev: 3.6520776163151066e-7",
            "extra": "mean: 2.1069812956964142 usec\nrounds: 53996"
          }
        ]
      }
    ]
  }
}