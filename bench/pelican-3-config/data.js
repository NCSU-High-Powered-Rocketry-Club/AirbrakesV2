window.BENCHMARK_DATA = {
  "lastUpdate": 1743810420396,
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
          "id": "1125992f1c8eb211a7c98ad86071a3d97ae55fc8",
          "message": "Switch to Pelicanator Launch 3 config",
          "timestamp": "2025-04-01T22:12:07Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/186/commits/1125992f1c8eb211a7c98ad86071a3d97ae55fc8"
        },
        "date": 1743810408208,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6308.467562315563,
            "unit": "iter/sec",
            "range": "stddev: 0.000004672777552018719",
            "extra": "mean: 158.51710262784385 usec\nrounds: 1598"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 280199.3876585732,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034025428755483677",
            "extra": "mean: 3.568887171225776 usec\nrounds: 9962"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 805368.6299910491,
            "unit": "iter/sec",
            "range": "stddev: 1.3601461395584737e-7",
            "extra": "mean: 1.2416674337205238 usec\nrounds: 101297"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 520.5675500029037,
            "unit": "iter/sec",
            "range": "stddev: 0.0003694079480592887",
            "extra": "mean: 1.920980283912092 msec\nrounds: 634"
          }
        ]
      }
    ]
  }
}