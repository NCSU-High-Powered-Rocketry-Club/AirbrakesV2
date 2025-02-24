window.BENCHMARK_DATA = {
  "lastUpdate": 1740432440741,
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
      }
    ]
  }
}