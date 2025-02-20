window.BENCHMARK_DATA = {
  "lastUpdate": 1740032193032,
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
      }
    ]
  }
}