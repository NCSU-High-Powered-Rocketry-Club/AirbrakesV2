window.BENCHMARK_DATA = {
  "lastUpdate": 1744165096572,
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
          "id": "32c741ca4625e7df2415c9099dced08917c12201",
          "message": "Revert \"Servo rewrite launch day\"",
          "timestamp": "2025-04-09T00:49:09Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/193/commits/32c741ca4625e7df2415c9099dced08917c12201"
        },
        "date": 1744165009640,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6338.718750140849,
            "unit": "iter/sec",
            "range": "stddev: 0.000004523651222530615",
            "extra": "mean: 157.76058844348938 usec\nrounds: 1696"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 285202.4177193686,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033336052286429527",
            "extra": "mean: 3.506281636728524 usec\nrounds: 10265"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808347.1464950342,
            "unit": "iter/sec",
            "range": "stddev: 1.4026580799844846e-7",
            "extra": "mean: 1.2370922620757259 usec\nrounds: 131441"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 556.6869040747316,
            "unit": "iter/sec",
            "range": "stddev: 0.0005846999335162923",
            "extra": "mean: 1.796341880292834 msec\nrounds: 685"
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
          "id": "d538a8d0425c7ef906899d3b8d1ee0a9408b6a22",
          "message": "Revert \"Servo rewrite launch day\"",
          "timestamp": "2025-04-09T00:49:09Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/193/commits/d538a8d0425c7ef906899d3b8d1ee0a9408b6a22"
        },
        "date": 1744165083469,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6378.395309622656,
            "unit": "iter/sec",
            "range": "stddev: 0.000004134937982248274",
            "extra": "mean: 156.77924485040418 usec\nrounds: 1699"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 281908.48865150905,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032947771740405998",
            "extra": "mean: 3.547250403077378 usec\nrounds: 9928"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808077.9056688135,
            "unit": "iter/sec",
            "range": "stddev: 9.464208504784154e-8",
            "extra": "mean: 1.237504444787833 usec\nrounds: 110914"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 602.1732851462211,
            "unit": "iter/sec",
            "range": "stddev: 0.0007328836084818215",
            "extra": "mean: 1.6606515510849633 msec\nrounds: 646"
          }
        ]
      }
    ]
  }
}