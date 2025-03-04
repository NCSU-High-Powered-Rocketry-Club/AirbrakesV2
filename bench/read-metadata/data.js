window.BENCHMARK_DATA = {
  "lastUpdate": 1741107693138,
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
          "id": "46f606965245059fc975f70af848cb329b18904f",
          "message": "`MockIMU` upgrades, `--mock-servo` & `--mock-camera` for `uv run real`",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/166/commits/46f606965245059fc975f70af848cb329b18904f"
        },
        "date": 1740967233456,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1073.604177857691,
            "unit": "iter/sec",
            "range": "stddev: 0.0008774110764639791",
            "extra": "mean: 931.4419789194902 usec\nrounds: 427"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3240.324180264093,
            "unit": "iter/sec",
            "range": "stddev: 0.0000163065942143422",
            "extra": "mean: 308.61109702872324 usec\nrounds: 1783"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 134272.88577491,
            "unit": "iter/sec",
            "range": "stddev: 0.00000470237662109068",
            "extra": "mean: 7.447519983121255 usec\nrounds: 6831"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 511418.6223155609,
            "unit": "iter/sec",
            "range": "stddev: 4.786379702030691e-7",
            "extra": "mean: 1.9553453010222406 usec\nrounds: 30304"
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
          "id": "3bbc1dc1402a1b2b8d5c7b0ed2525edfc399f73a",
          "message": "`MockIMU` upgrades, `--mock-servo` & `--mock-camera` for `uv run real`",
          "timestamp": "2025-03-04T05:18:40Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/166/commits/3bbc1dc1402a1b2b8d5c7b0ed2525edfc399f73a"
        },
        "date": 1741107678343,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1084.2603557108396,
            "unit": "iter/sec",
            "range": "stddev: 0.000873182999261413",
            "extra": "mean: 922.287709527479 usec\nrounds: 420"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3180.1489553966526,
            "unit": "iter/sec",
            "range": "stddev: 0.000018316507856435314",
            "extra": "mean: 314.45067952022146 usec\nrounds: 1582"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151936.2200210097,
            "unit": "iter/sec",
            "range": "stddev: 0.000020236961857606808",
            "extra": "mean: 6.581709087284916 usec\nrounds: 8958"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 514780.30702504644,
            "unit": "iter/sec",
            "range": "stddev: 3.891328853409389e-7",
            "extra": "mean: 1.9425762531186832 usec\nrounds: 65617"
          }
        ]
      }
    ]
  }
}