window.BENCHMARK_DATA = {
  "lastUpdate": 1740813374857,
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
          "id": "367debb1e8ea2a607cf5bc403b51bf9cafe53fed",
          "message": "`MockIMU` upgrades, `--mock-servo` & `--mock-camera` for `uv run real`",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/166/commits/367debb1e8ea2a607cf5bc403b51bf9cafe53fed"
        },
        "date": 1740812956191,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1030.9945622362234,
            "unit": "iter/sec",
            "range": "stddev: 0.000871607950675819",
            "extra": "mean: 969.9372204553665 usec\nrounds: 440"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3256.4661880282124,
            "unit": "iter/sec",
            "range": "stddev: 0.00001361850571997197",
            "extra": "mean: 307.08133978983494 usec\nrounds: 1651"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 149548.12237563694,
            "unit": "iter/sec",
            "range": "stddev: 0.00000469262952691417",
            "extra": "mean: 6.686810801196065 usec\nrounds: 8034"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 513388.9197670312,
            "unit": "iter/sec",
            "range": "stddev: 3.4642327052719405e-7",
            "extra": "mean: 1.9478410255791774 usec\nrounds: 52084"
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
          "id": "da9cf1e9cc5ed460c5b01341e6cfda5a5b6e15e4",
          "message": "`MockIMU` upgrades, `--mock-servo` & `--mock-camera` for `uv run real`",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/166/commits/da9cf1e9cc5ed460c5b01341e6cfda5a5b6e15e4"
        },
        "date": 1740813358814,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1053.192220353614,
            "unit": "iter/sec",
            "range": "stddev: 0.0008652608047961843",
            "extra": "mean: 949.4942904764769 usec\nrounds: 451"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3192.5981592053404,
            "unit": "iter/sec",
            "range": "stddev: 0.000013263734958266945",
            "extra": "mean: 313.22451186556685 usec\nrounds: 1686"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151999.27915385374,
            "unit": "iter/sec",
            "range": "stddev: 0.000004717053070232727",
            "extra": "mean: 6.578978568627286 usec\nrounds: 8913"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 499033.83032165054,
            "unit": "iter/sec",
            "range": "stddev: 3.826728525284184e-7",
            "extra": "mean: 2.0038721610425756 usec\nrounds: 56180"
          }
        ]
      }
    ]
  }
}