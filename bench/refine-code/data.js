window.BENCHMARK_DATA = {
  "lastUpdate": 1740220678019,
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
          "id": "e7310b237b5fec7726008f1ad765043fa42a94c0",
          "message": "Refine code",
          "timestamp": "2025-02-22T07:28:35Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/158/commits/e7310b237b5fec7726008f1ad765043fa42a94c0"
        },
        "date": 1740210776602,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1073.0569221872167,
            "unit": "iter/sec",
            "range": "stddev: 0.000877901939559633",
            "extra": "mean: 931.9170114123074 usec\nrounds: 438"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3302.766611129439,
            "unit": "iter/sec",
            "range": "stddev: 0.000012853421357857399",
            "extra": "mean: 302.7764652307759 usec\nrounds: 1625"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 149871.37774518252,
            "unit": "iter/sec",
            "range": "stddev: 0.000004375448942987929",
            "extra": "mean: 6.672388117364485 usec\nrounds: 8348"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 492254.8575692291,
            "unit": "iter/sec",
            "range": "stddev: 4.0155891353001e-7",
            "extra": "mean: 2.0314680182904303 usec\nrounds: 35973"
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
          "id": "08dd7cba9667de967cac33d68a9e586cc4385c20",
          "message": "Refine code",
          "timestamp": "2025-02-22T07:28:35Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/158/commits/08dd7cba9667de967cac33d68a9e586cc4385c20"
        },
        "date": 1740220662158,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1040.60519372215,
            "unit": "iter/sec",
            "range": "stddev: 0.0008648905589516137",
            "extra": "mean: 960.9792513365143 usec\nrounds: 374"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3183.776083296887,
            "unit": "iter/sec",
            "range": "stddev: 0.00002264591158430863",
            "extra": "mean: 314.0924404974086 usec\nrounds: 1689"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 148014.60494333497,
            "unit": "iter/sec",
            "range": "stddev: 0.000004266684501484797",
            "extra": "mean: 6.756090051943414 usec\nrounds: 8273"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503110.57601561025,
            "unit": "iter/sec",
            "range": "stddev: 3.1838445786661237e-7",
            "extra": "mean: 1.987634622828864 usec\nrounds: 57078"
          }
        ]
      }
    ]
  }
}