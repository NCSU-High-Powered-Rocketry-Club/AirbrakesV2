window.BENCHMARK_DATA = {
  "lastUpdate": 1743402414441,
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
          "id": "bf38a67ecb95b820d2a4e5469b28b4dbf95ec029",
          "message": "Fix pitch calculations",
          "timestamp": "2025-03-29T17:11:50Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/185/commits/bf38a67ecb95b820d2a4e5469b28b4dbf95ec029"
        },
        "date": 1743401996428,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6393.507930964806,
            "unit": "iter/sec",
            "range": "stddev: 0.0000040484847539921275",
            "extra": "mean: 156.4086587203304 usec\nrounds: 1594"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 279752.3654136747,
            "unit": "iter/sec",
            "range": "stddev: 0.000003388814484875302",
            "extra": "mean: 3.574589971817692 usec\nrounds: 9892"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 800646.6387853016,
            "unit": "iter/sec",
            "range": "stddev: 1.2820978891612413e-7",
            "extra": "mean: 1.24899044292142 usec\nrounds: 118134"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 540.9121386015447,
            "unit": "iter/sec",
            "range": "stddev: 0.0005108605325211506",
            "extra": "mean: 1.848729079338772 msec\nrounds: 605"
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
          "id": "8a51815bf0bae7ad1cadb5f5791225b28d2e933c",
          "message": "Fix pitch calculations",
          "timestamp": "2025-03-29T17:11:50Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/185/commits/8a51815bf0bae7ad1cadb5f5791225b28d2e933c"
        },
        "date": 1743402400042,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3020.572945064391,
            "unit": "iter/sec",
            "range": "stddev: 0.000023329742797489176",
            "extra": "mean: 331.0630195619005 usec\nrounds: 1227"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 119511.16962498207,
            "unit": "iter/sec",
            "range": "stddev: 0.000006949563180731105",
            "extra": "mean: 8.367418736992803 usec\nrounds: 6842"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 477180.79061349214,
            "unit": "iter/sec",
            "range": "stddev: 3.2105737047671293e-7",
            "extra": "mean: 2.0956417770177636 usec\nrounds: 60976"
          },
          {
            "name": "tests/test_context.py::TestContext::test_benchmark_airbrakes_update",
            "value": 770.7966074795148,
            "unit": "iter/sec",
            "range": "stddev: 0.0009099587515811341",
            "extra": "mean: 1.2973591091299355 msec\nrounds: 449"
          }
        ]
      }
    ]
  }
}