window.BENCHMARK_DATA = {
  "lastUpdate": 1740085657539,
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
          "id": "ab2b844ed3331dfabb57f40a0e2850b7047169c2",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/ab2b844ed3331dfabb57f40a0e2850b7047169c2"
        },
        "date": 1740032176726,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1633.752920788778,
            "unit": "iter/sec",
            "range": "stddev: 0.00038910511709238906",
            "extra": "mean: 612.0876585898917 usec\nrounds: 413"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3144.8813273707533,
            "unit": "iter/sec",
            "range": "stddev: 0.000029284588905975403",
            "extra": "mean: 317.97702231137606 usec\nrounds: 1703"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 141951.99433086158,
            "unit": "iter/sec",
            "range": "stddev: 0.000003429681784608877",
            "extra": "mean: 7.044635087473311 usec\nrounds: 7813"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 479055.2553704122,
            "unit": "iter/sec",
            "range": "stddev: 4.876748871012223e-7",
            "extra": "mean: 2.0874418739583307 usec\nrounds: 47439"
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
          "id": "43f3f5334543b584c06ceabd5d0ab4fcca80edf0",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/43f3f5334543b584c06ceabd5d0ab4fcca80edf0"
        },
        "date": 1740085641934,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1622.8773664288483,
            "unit": "iter/sec",
            "range": "stddev: 0.00040796383508207934",
            "extra": "mean: 616.1895043249671 usec\nrounds: 462"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3254.9512718365017,
            "unit": "iter/sec",
            "range": "stddev: 0.000017088538546076782",
            "extra": "mean: 307.2242612823454 usec\nrounds: 1684"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 136251.69075792254,
            "unit": "iter/sec",
            "range": "stddev: 0.000003619340652842856",
            "extra": "mean: 7.339358465479106 usec\nrounds: 7069"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 511645.35285870713,
            "unit": "iter/sec",
            "range": "stddev: 4.017920278252442e-7",
            "extra": "mean: 1.9544788092234542 usec\nrounds: 49408"
          }
        ]
      }
    ]
  }
}