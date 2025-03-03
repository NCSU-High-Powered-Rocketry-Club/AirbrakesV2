window.BENCHMARK_DATA = {
  "lastUpdate": 1740971028061,
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
          "id": "a6fa3aaa318832a2487cb3a4a4cf6263d4cabd48",
          "message": "Imu optimization",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/168/commits/a6fa3aaa318832a2487cb3a4a4cf6263d4cabd48"
        },
        "date": 1740970594365,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 979.8041474612527,
            "unit": "iter/sec",
            "range": "stddev: 0.0008786297576347066",
            "extra": "mean: 1.020612132119543 msec\nrounds: 439"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3220.483317163356,
            "unit": "iter/sec",
            "range": "stddev: 0.000023256564955400976",
            "extra": "mean: 310.5123987665346 usec\nrounds: 1620"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 139250.2378620224,
            "unit": "iter/sec",
            "range": "stddev: 0.000004545304801572193",
            "extra": "mean: 7.181316278905468 usec\nrounds: 7310"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 436738.8254487798,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015063945355634633",
            "extra": "mean: 2.289697965305534 usec\nrounds: 51653"
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
          "id": "420fb05accce000e692bb48e1651f5c1eb7df799",
          "message": "Imu optimization",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/168/commits/420fb05accce000e692bb48e1651f5c1eb7df799"
        },
        "date": 1740971012725,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1003.435078428845,
            "unit": "iter/sec",
            "range": "stddev: 0.0009043983323702686",
            "extra": "mean: 996.576680940611 usec\nrounds: 467"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3207.04900307671,
            "unit": "iter/sec",
            "range": "stddev: 0.000010816822655409766",
            "extra": "mean: 311.8131338313326 usec\nrounds: 1741"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 158191.12959313043,
            "unit": "iter/sec",
            "range": "stddev: 0.000004286240007895414",
            "extra": "mean: 6.321466965764848 usec\nrounds: 9778"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 488895.2590780412,
            "unit": "iter/sec",
            "range": "stddev: 3.142019627763783e-7",
            "extra": "mean: 2.04542789366745 usec\nrounds: 71429"
          }
        ]
      }
    ]
  }
}