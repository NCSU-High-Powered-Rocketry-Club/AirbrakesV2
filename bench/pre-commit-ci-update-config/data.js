window.BENCHMARK_DATA = {
  "lastUpdate": 1744047333580,
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
          "id": "3b7795a10e14b0ef237ee7a88fd1085cb47ace42",
          "message": "[pre-commit.ci] pre-commit autoupdate",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/169/commits/3b7795a10e14b0ef237ee7a88fd1085cb47ace42"
        },
        "date": 1741023317501,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1083.2794741534021,
            "unit": "iter/sec",
            "range": "stddev: 0.0008577779652407979",
            "extra": "mean: 923.122817204225 usec\nrounds: 465"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3188.9527194440716,
            "unit": "iter/sec",
            "range": "stddev: 0.000016564874833188082",
            "extra": "mean: 313.5825733328306 usec\nrounds: 1650"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 146368.72436730663,
            "unit": "iter/sec",
            "range": "stddev: 0.000004429525369781012",
            "extra": "mean: 6.832060635375484 usec\nrounds: 8312"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 502703.69703678234,
            "unit": "iter/sec",
            "range": "stddev: 4.3554272372423914e-7",
            "extra": "mean: 1.989243377151513 usec\nrounds: 34917"
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
          "id": "971223954ec11de7163538d3fa9e186a9f21f693",
          "message": "[pre-commit.ci] pre-commit autoupdate",
          "timestamp": "2025-04-05T16:39:10Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/190/commits/971223954ec11de7163538d3fa9e186a9f21f693"
        },
        "date": 1744047321067,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6265.311157546551,
            "unit": "iter/sec",
            "range": "stddev: 0.000013541690614587718",
            "extra": "mean: 159.6089922518058 usec\nrounds: 1549"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 260982.03885153192,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037058279918918462",
            "extra": "mean: 3.831681308033931 usec\nrounds: 9266"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 765179.4198600253,
            "unit": "iter/sec",
            "range": "stddev: 3.709978814734558e-7",
            "extra": "mean: 1.3068830316724025 usec\nrounds: 118921"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 573.6400797911173,
            "unit": "iter/sec",
            "range": "stddev: 0.0006422665043171193",
            "extra": "mean: 1.7432533660551326 msec\nrounds: 489"
          }
        ]
      }
    ]
  }
}