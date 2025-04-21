window.BENCHMARK_DATA = {
  "lastUpdate": 1745219624670,
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
          "id": "e6a7f88066024aac4191bbb427c769146ec1c87c",
          "message": "Use polars instead of pandas for much faster file read",
          "timestamp": "2025-04-20T21:33:42Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/197/commits/e6a7f88066024aac4191bbb427c769146ec1c87c"
        },
        "date": 1745219612154,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 24581.42884677663,
            "unit": "iter/sec",
            "range": "stddev: 0.000002000404323089309",
            "extra": "mean: 40.68111769390209 usec\nrounds: 2464"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 273834.78706871247,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042823133165825445",
            "extra": "mean: 3.6518369733246248 usec\nrounds: 9569"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 809262.1438603499,
            "unit": "iter/sec",
            "range": "stddev: 1.58549863933566e-7",
            "extra": "mean: 1.2356935358792276 usec\nrounds: 126775"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 643.4151043362023,
            "unit": "iter/sec",
            "range": "stddev: 0.0008143650700757656",
            "extra": "mean: 1.554206597359381 msec\nrounds: 683"
          }
        ]
      }
    ]
  }
}