window.BENCHMARK_DATA = {
  "lastUpdate": 1741403335526,
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
          "id": "2e0e2ece2d79ce41ec360d1c674074e5a0d3dfef",
          "message": "Revert \"Added altitude and vel fix for when airbrakes deploy\"",
          "timestamp": "2025-03-06T03:55:58Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/175/commits/2e0e2ece2d79ce41ec360d1c674074e5a0d3dfef"
        },
        "date": 1741403318138,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1048.3197873421827,
            "unit": "iter/sec",
            "range": "stddev: 0.0009022999660373965",
            "extra": "mean: 953.9073974128748 usec\nrounds: 463"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3258.9262560764673,
            "unit": "iter/sec",
            "range": "stddev: 0.000026991589476268236",
            "extra": "mean: 306.8495330741034 usec\nrounds: 1814"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 150095.87081679143,
            "unit": "iter/sec",
            "range": "stddev: 0.000018377918186635655",
            "extra": "mean: 6.6624084630589895 usec\nrounds: 8816"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 512737.47810463083,
            "unit": "iter/sec",
            "range": "stddev: 7.46234608060671e-7",
            "extra": "mean: 1.9503157906392339 usec\nrounds: 98426"
          }
        ]
      }
    ]
  }
}