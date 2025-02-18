window.BENCHMARK_DATA = {
  "lastUpdate": 1739916922943,
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
          "id": "bc8fbb2530ba28adb7f9902a475de50d9a427a8c",
          "message": "Remove Windows support",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/155/commits/bc8fbb2530ba28adb7f9902a475de50d9a427a8c"
        },
        "date": 1739504946036,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1270.1307294281596,
            "unit": "iter/sec",
            "range": "stddev: 0.00035539317637893475",
            "extra": "mean: 787.320530737983 usec\nrounds: 488"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6410.882745062336,
            "unit": "iter/sec",
            "range": "stddev: 0.000006333296244137533",
            "extra": "mean: 155.98475900533361 usec\nrounds: 2332"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 281491.99184191844,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025214951440687313",
            "extra": "mean: 3.552498930632402 usec\nrounds: 10288"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 801651.5803452843,
            "unit": "iter/sec",
            "range": "stddev: 2.768359462872381e-7",
            "extra": "mean: 1.247424722308018 usec\nrounds: 87589"
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
          "id": "4f539001b2bee7de07cceb3eede01ec9abf406c4",
          "message": "Remove Windows support",
          "timestamp": "2025-02-18T22:11:02Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/155/commits/4f539001b2bee7de07cceb3eede01ec9abf406c4"
        },
        "date": 1739916907783,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1636.6477657603687,
            "unit": "iter/sec",
            "range": "stddev: 0.0004029641008384867",
            "extra": "mean: 611.005019479809 usec\nrounds: 462"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3287.2430970952764,
            "unit": "iter/sec",
            "range": "stddev: 0.000013717299219308149",
            "extra": "mean: 304.206281818231 usec\nrounds: 1650"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 138072.75925967,
            "unit": "iter/sec",
            "range": "stddev: 0.0000040422750975633735",
            "extra": "mean: 7.24255823785867 usec\nrounds: 7083"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 510538.1046969308,
            "unit": "iter/sec",
            "range": "stddev: 3.983600171023445e-7",
            "extra": "mean: 1.9587176565275712 usec\nrounds: 76453"
          }
        ]
      }
    ]
  }
}