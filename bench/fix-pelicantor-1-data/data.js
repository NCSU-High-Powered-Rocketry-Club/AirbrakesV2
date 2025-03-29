window.BENCHMARK_DATA = {
  "lastUpdate": 1743266486621,
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
          "id": "a92066e7d72dcaad653c4ae0360bc08020284c18",
          "message": "Fix unix timestamp on pelicanator launch 1",
          "timestamp": "2025-03-26T21:35:35Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/184/commits/a92066e7d72dcaad653c4ae0360bc08020284c18"
        },
        "date": 1743266472214,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 2980.786410123788,
            "unit": "iter/sec",
            "range": "stddev: 0.000025526106150688116",
            "extra": "mean: 335.4819374523623 usec\nrounds: 1295"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 107055.10045718102,
            "unit": "iter/sec",
            "range": "stddev: 0.000002994418756823572",
            "extra": "mean: 9.340984182252685 usec\nrounds: 5753"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 482175.2454632989,
            "unit": "iter/sec",
            "range": "stddev: 6.074302055668717e-7",
            "extra": "mean: 2.073934755898031 usec\nrounds: 57737"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 931.7839180082782,
            "unit": "iter/sec",
            "range": "stddev: 0.0009094949172193784",
            "extra": "mean: 1.073210194631322 msec\nrounds: 447"
          }
        ]
      }
    ]
  }
}