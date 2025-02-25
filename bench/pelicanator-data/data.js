window.BENCHMARK_DATA = {
  "lastUpdate": 1740498326940,
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
          "id": "12b10bb56c55157cd328037cf825d8d931df9426",
          "message": "Add pelicanator launch and fix mock",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/164/commits/12b10bb56c55157cd328037cf825d8d931df9426"
        },
        "date": 1740432424522,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1089.9499556598182,
            "unit": "iter/sec",
            "range": "stddev: 0.0008767698847716115",
            "extra": "mean: 917.4733159144307 usec\nrounds: 421"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3169.9742934878477,
            "unit": "iter/sec",
            "range": "stddev: 0.000018991669872825126",
            "extra": "mean: 315.4599714118577 usec\nrounds: 1644"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 153279.12701983153,
            "unit": "iter/sec",
            "range": "stddev: 0.0000045783255000287225",
            "extra": "mean: 6.524045507322195 usec\nrounds: 8592"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 509697.0408276069,
            "unit": "iter/sec",
            "range": "stddev: 3.2816415463250383e-7",
            "extra": "mean: 1.9619497856536048 usec\nrounds: 58549"
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
          "id": "d761fe4120e2c5b8a0edb8c2d81177da57dacdcd",
          "message": "Add pelicanator launch and fix mock",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/164/commits/d761fe4120e2c5b8a0edb8c2d81177da57dacdcd"
        },
        "date": 1740498310852,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1005.8128265861188,
            "unit": "iter/sec",
            "range": "stddev: 0.0008767812762348794",
            "extra": "mean: 994.2207670925729 usec\nrounds: 468"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3294.6223898963226,
            "unit": "iter/sec",
            "range": "stddev: 0.00001278291966292667",
            "extra": "mean: 303.52492081238745 usec\nrounds: 1869"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 165075.3880133126,
            "unit": "iter/sec",
            "range": "stddev: 0.000004011465459434507",
            "extra": "mean: 6.057838252176966 usec\nrounds: 9793"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 510267.10223174863,
            "unit": "iter/sec",
            "range": "stddev: 4.070131882869087e-7",
            "extra": "mean: 1.9597579299670957 usec\nrounds: 76924"
          }
        ]
      }
    ]
  }
}