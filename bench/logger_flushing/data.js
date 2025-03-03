window.BENCHMARK_DATA = {
  "lastUpdate": 1741039541267,
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
          "id": "51a98251cdd1c6439b7249e8810b853dd9224fcb",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/51a98251cdd1c6439b7249e8810b853dd9224fcb"
        },
        "date": 1740345851636,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 984.8632822099753,
            "unit": "iter/sec",
            "range": "stddev: 0.000864534862962819",
            "extra": "mean: 1.015369359446581 msec\nrounds: 434"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3106.5294135173185,
            "unit": "iter/sec",
            "range": "stddev: 0.00001783503328814815",
            "extra": "mean: 321.9026337393554 usec\nrounds: 1559"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 131503.0343418168,
            "unit": "iter/sec",
            "range": "stddev: 0.000004423099756546365",
            "extra": "mean: 7.604387267602456 usec\nrounds: 6990"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503455.00051847094,
            "unit": "iter/sec",
            "range": "stddev: 3.7311162671948827e-7",
            "extra": "mean: 1.986274838804211 usec\nrounds: 62815"
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
          "id": "bdaba21282c803117642c88abd5e26fc38128808",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/bdaba21282c803117642c88abd5e26fc38128808"
        },
        "date": 1740951471869,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1037.0518687569725,
            "unit": "iter/sec",
            "range": "stddev: 0.0008396332975129279",
            "extra": "mean: 964.2719232535751 usec\nrounds: 430"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3265.55774814378,
            "unit": "iter/sec",
            "range": "stddev: 0.00001532281861168563",
            "extra": "mean: 306.22640208044817 usec\nrounds: 1634"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151617.7368810659,
            "unit": "iter/sec",
            "range": "stddev: 0.000004300289750782662",
            "extra": "mean: 6.5955344049518025 usec\nrounds: 8458"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 511955.346187613,
            "unit": "iter/sec",
            "range": "stddev: 4.186621559184496e-7",
            "extra": "mean: 1.9532953556334902 usec\nrounds: 49801"
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
          "id": "d5c248d7e7cb538964c669f4b4ba6698b60cb581",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-03-03T18:11:51Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/d5c248d7e7cb538964c669f4b4ba6698b60cb581"
        },
        "date": 1741039525166,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1020.3115058511072,
            "unit": "iter/sec",
            "range": "stddev: 0.0009041785627826705",
            "extra": "mean: 980.0928385746626 usec\nrounds: 477"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3266.473553244376,
            "unit": "iter/sec",
            "range": "stddev: 0.000012114403397960541",
            "extra": "mean: 306.14054689246296 usec\nrounds: 1770"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 157418.9762701695,
            "unit": "iter/sec",
            "range": "stddev: 0.000004282208167076774",
            "extra": "mean: 6.35247429308494 usec\nrounds: 9161"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 510736.6375044614,
            "unit": "iter/sec",
            "range": "stddev: 3.4752611179151837e-7",
            "extra": "mean: 1.957956266631185 usec\nrounds: 62035"
          }
        ]
      }
    ]
  }
}