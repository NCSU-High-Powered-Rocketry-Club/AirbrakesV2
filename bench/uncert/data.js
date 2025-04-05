window.BENCHMARK_DATA = {
  "lastUpdate": 1743814936825,
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
          "id": "08f67c69d46d4264292908254c2eab8535274239",
          "message": "Changing Convergence Thresholds",
          "timestamp": "2025-04-01T22:12:07Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/187/commits/08f67c69d46d4264292908254c2eab8535274239"
        },
        "date": 1743814924439,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6407.925545645673,
            "unit": "iter/sec",
            "range": "stddev: 0.0000051262615100479724",
            "extra": "mean: 156.05674455433117 usec\nrounds: 1699"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 273551.28478911816,
            "unit": "iter/sec",
            "range": "stddev: 0.0000038883584503567836",
            "extra": "mean: 3.6556216534347636 usec\nrounds: 9523"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 807495.4310038242,
            "unit": "iter/sec",
            "range": "stddev: 1.1128727349167232e-7",
            "extra": "mean: 1.238397099977231 usec\nrounds: 109927"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 541.7084894640873,
            "unit": "iter/sec",
            "range": "stddev: 0.0005078109293803222",
            "extra": "mean: 1.8460113131867304 msec\nrounds: 546"
          }
        ]
      }
    ]
  }
}