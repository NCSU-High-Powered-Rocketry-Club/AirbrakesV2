window.BENCHMARK_DATA = {
  "lastUpdate": 1744592524300,
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
          "id": "1cf7e2dd5269556aa373c908750b55cca5f3c1bb",
          "message": "Vectorize `calculate_rotated_accelerations`, more performance improvements",
          "timestamp": "2025-04-09T07:01:13Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/195/commits/1cf7e2dd5269556aa373c908750b55cca5f3c1bb"
        },
        "date": 1744592511326,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 24560.169185064377,
            "unit": "iter/sec",
            "range": "stddev: 0.000001966562168809904",
            "extra": "mean: 40.716331897588226 usec\nrounds: 2308"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 244413.56289556288,
            "unit": "iter/sec",
            "range": "stddev: 0.000003753151046852186",
            "extra": "mean: 4.091425975518784 usec\nrounds: 7599"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808071.8393887497,
            "unit": "iter/sec",
            "range": "stddev: 1.2057465981928882e-7",
            "extra": "mean: 1.2375137348635126 usec\nrounds: 114273"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 680.5801015511536,
            "unit": "iter/sec",
            "range": "stddev: 0.0008648389274317129",
            "extra": "mean: 1.4693347597451587 msec\nrounds: 641"
          }
        ]
      }
    ]
  }
}