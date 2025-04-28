window.BENCHMARK_DATA = {
  "lastUpdate": 1745827377869,
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
      },
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
          "id": "45269df1a9127ad9d6168a4fe545a25c3a32af8b",
          "message": "Use polars instead of pandas for much faster file read",
          "timestamp": "2025-04-20T21:33:42Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/197/commits/45269df1a9127ad9d6168a4fe545a25c3a32af8b"
        },
        "date": 1745261681499,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 24205.022760626263,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031138499085085437",
            "extra": "mean: 41.31373929656767 usec\nrounds: 2359"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 271739.0095643735,
            "unit": "iter/sec",
            "range": "stddev: 0.000007035354847265298",
            "extra": "mean: 3.6800016368761566 usec\nrounds: 9773"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 798302.3253577276,
            "unit": "iter/sec",
            "range": "stddev: 1.750570414842366e-7",
            "extra": "mean: 1.2526582576994119 usec\nrounds: 112816"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 619.6912972919191,
            "unit": "iter/sec",
            "range": "stddev: 0.0007709444926318487",
            "extra": "mean: 1.6137067026276604 msec\nrounds: 723"
          }
        ]
      },
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
          "id": "efe636af2406df5c2f9e441ac55cbb29e3ac132b",
          "message": "Use polars instead of pandas for much faster file read",
          "timestamp": "2025-04-20T21:33:42Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/197/commits/efe636af2406df5c2f9e441ac55cbb29e3ac132b"
        },
        "date": 1745827365093,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 24702.472329309858,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016922559805661095",
            "extra": "mean: 40.481777964122436 usec\nrounds: 2387"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 267923.9832837336,
            "unit": "iter/sec",
            "range": "stddev: 0.000006619019859083362",
            "extra": "mean: 3.732401958733915 usec\nrounds: 9496"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808141.4347329835,
            "unit": "iter/sec",
            "range": "stddev: 1.3546042556287555e-7",
            "extra": "mean: 1.2374071629310879 usec\nrounds: 20412"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 1034.3642704184465,
            "unit": "iter/sec",
            "range": "stddev: 0.0009657830643461246",
            "extra": "mean: 966.7773999922247 usec\nrounds: 5"
          }
        ]
      }
    ]
  }
}