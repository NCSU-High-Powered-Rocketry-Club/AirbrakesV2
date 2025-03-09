window.BENCHMARK_DATA = {
  "lastUpdate": 1741484444819,
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
          "id": "33a8e10dad3bf4250e37469d03656ae40104fdfb",
          "message": "Add Pelicanator launch 2 data",
          "timestamp": "2025-03-08T03:10:21Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/177/commits/33a8e10dad3bf4250e37469d03656ae40104fdfb"
        },
        "date": 1741484431120,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 671.0267158327325,
            "unit": "iter/sec",
            "range": "stddev: 0.0007768700108256384",
            "extra": "mean: 1.490253631346134 msec\nrounds: 453"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3234.5126251505285,
            "unit": "iter/sec",
            "range": "stddev: 0.000011369559728052577",
            "extra": "mean: 309.1655887271307 usec\nrounds: 1792"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 150246.7417571663,
            "unit": "iter/sec",
            "range": "stddev: 0.000018643041655307558",
            "extra": "mean: 6.655718375685195 usec\nrounds: 9431"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 484267.07873499347,
            "unit": "iter/sec",
            "range": "stddev: 2.922369366282456e-7",
            "extra": "mean: 2.064976216455202 usec\nrounds: 91576"
          }
        ]
      }
    ]
  }
}