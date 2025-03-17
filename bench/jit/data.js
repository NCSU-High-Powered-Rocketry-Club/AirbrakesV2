window.BENCHMARK_DATA = {
  "lastUpdate": 1742174869960,
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
          "id": "7958c3753de07992a01b98fe9789f08cf39d6b1e",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/7958c3753de07992a01b98fe9789f08cf39d6b1e"
        },
        "date": 1742170495823,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 930.9402800750868,
            "unit": "iter/sec",
            "range": "stddev: 0.000898569543012286",
            "extra": "mean: 1.0741827605948504 msec\nrounds: 472"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3243.709701897205,
            "unit": "iter/sec",
            "range": "stddev: 0.000011358269010078706",
            "extra": "mean: 308.28899374537514 usec\nrounds: 1759"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 159510.00292992996,
            "unit": "iter/sec",
            "range": "stddev: 0.00001685551715467629",
            "extra": "mean: 6.269199308079024 usec\nrounds: 10110"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 506432.7607918123,
            "unit": "iter/sec",
            "range": "stddev: 2.6980527891572e-7",
            "extra": "mean: 1.9745957951782003 usec\nrounds: 94697"
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
          "id": "a64ba81b7796d817ad0aba934a5732a8ff8eef68",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/a64ba81b7796d817ad0aba934a5732a8ff8eef68"
        },
        "date": 1742170719185,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1087.3428509437374,
            "unit": "iter/sec",
            "range": "stddev: 0.0008648683332602033",
            "extra": "mean: 919.6731271393104 usec\nrounds: 409"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 2961.3457813150367,
            "unit": "iter/sec",
            "range": "stddev: 0.000026486395071682658",
            "extra": "mean: 337.6843076920024 usec\nrounds: 1534"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 123182.57204639073,
            "unit": "iter/sec",
            "range": "stddev: 0.000006376706392266044",
            "extra": "mean: 8.118031498996453 usec\nrounds: 7397"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 467179.36067953275,
            "unit": "iter/sec",
            "range": "stddev: 3.8756509421489e-7",
            "extra": "mean: 2.140505519219549 usec\nrounds: 48829"
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
          "id": "c0bb455116a2d6b673db6fe252baad99a51cb497",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/c0bb455116a2d6b673db6fe252baad99a51cb497"
        },
        "date": 1742172788442,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1060.6995629451421,
            "unit": "iter/sec",
            "range": "stddev: 0.0008633619643435697",
            "extra": "mean: 942.7740285132168 usec\nrounds: 491"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3209.173687708369,
            "unit": "iter/sec",
            "range": "stddev: 0.000012713263788612639",
            "extra": "mean: 311.6066929721362 usec\nrounds: 1736"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 156396.11365754443,
            "unit": "iter/sec",
            "range": "stddev: 0.000005037045257860263",
            "extra": "mean: 6.394020775923295 usec\nrounds: 9434"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503925.7700193594,
            "unit": "iter/sec",
            "range": "stddev: 3.524486585228871e-7",
            "extra": "mean: 1.9844192527831683 usec\nrounds: 84746"
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
          "id": "74c20ef6025b7b4b6b2ab8f14bf1cbb8bd93f456",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/74c20ef6025b7b4b6b2ab8f14bf1cbb8bd93f456"
        },
        "date": 1742174856038,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1024.5676674474196,
            "unit": "iter/sec",
            "range": "stddev: 0.0008886343850379206",
            "extra": "mean: 976.021430084138 usec\nrounds: 472"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3282.396744592817,
            "unit": "iter/sec",
            "range": "stddev: 0.000012094605658619994",
            "extra": "mean: 304.65543254249434 usec\nrounds: 1727"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 143430.448454874,
            "unit": "iter/sec",
            "range": "stddev: 0.000005013749054791214",
            "extra": "mean: 6.972020312093074 usec\nrounds: 7779"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 518079.976043218,
            "unit": "iter/sec",
            "range": "stddev: 4.0469062897425333e-7",
            "extra": "mean: 1.930203918779869 usec\nrounds: 47259"
          }
        ]
      }
    ]
  }
}