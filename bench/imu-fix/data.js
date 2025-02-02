window.BENCHMARK_DATA = {
  "lastUpdate": 1738461406699,
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
          "id": "eb77ab2606f0c59f7f5eb1b3c76b2d1722d06e79",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/eb77ab2606f0c59f7f5eb1b3c76b2d1722d06e79"
        },
        "date": 1738459613027,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1608.7799236938386,
            "unit": "iter/sec",
            "range": "stddev: 0.00042934583721102027",
            "extra": "mean: 621.5890596794311 usec\nrounds: 554"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6434.982690955376,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049306034970596685",
            "extra": "mean: 155.40057340100384 usec\nrounds: 2726"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 234245.3623030516,
            "unit": "iter/sec",
            "range": "stddev: 0.000002183842930917505",
            "extra": "mean: 4.269027954996456 usec\nrounds: 13577"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 464204.8775328276,
            "unit": "iter/sec",
            "range": "stddev: 1.5594281505474146e-7",
            "extra": "mean: 2.1542212251513493 usec\nrounds: 142369"
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
          "id": "dc97ca2d63b73bb77c8bea9641019636d06318e4",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/dc97ca2d63b73bb77c8bea9641019636d06318e4"
        },
        "date": 1738459915444,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 9.920040603965012,
            "unit": "iter/sec",
            "range": "stddev: 0.00019605060282852752",
            "extra": "mean: 100.80603899950802 msec\nrounds: 10"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6456.857688553687,
            "unit": "iter/sec",
            "range": "stddev: 0.000006058620220900978",
            "extra": "mean: 154.8740963847999 usec\nrounds: 2636"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 231148.6422051194,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022242297480824186",
            "extra": "mean: 4.326220523989097 usec\nrounds: 12311"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 481467.2467316386,
            "unit": "iter/sec",
            "range": "stddev: 1.585542963535546e-7",
            "extra": "mean: 2.076984481890172 usec\nrounds: 113418"
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
          "id": "bc686e038dff22498aaf525d978ebb828bd0a348",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/bc686e038dff22498aaf525d978ebb828bd0a348"
        },
        "date": 1738460220379,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 9.936844338758384,
            "unit": "iter/sec",
            "range": "stddev: 0.00010204411651261942",
            "extra": "mean: 100.63557060057065 msec\nrounds: 10"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6503.062707765694,
            "unit": "iter/sec",
            "range": "stddev: 0.000006711463001450926",
            "extra": "mean: 153.77369786175373 usec\nrounds: 2731"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 231359.54515856685,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023776128855815",
            "extra": "mean: 4.322276823783649 usec\nrounds: 13457"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 463323.1189492553,
            "unit": "iter/sec",
            "range": "stddev: 1.4132800704242627e-7",
            "extra": "mean: 2.1583209624156985 usec\nrounds: 122775"
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
          "id": "e6d1bfab19174a3f0e330164f6522c06558ee1ad",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/e6d1bfab19174a3f0e330164f6522c06558ee1ad"
        },
        "date": 1738461393143,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1301.0033360914879,
            "unit": "iter/sec",
            "range": "stddev: 0.0003737290604298654",
            "extra": "mean: 768.6375370905882 usec\nrounds: 538"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6398.553503801455,
            "unit": "iter/sec",
            "range": "stddev: 0.000005845143649527004",
            "extra": "mean: 156.28532283208827 usec\nrounds: 2952"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 235850.3757962604,
            "unit": "iter/sec",
            "range": "stddev: 0.000002228946314495889",
            "extra": "mean: 4.2399762842178 usec\nrounds: 13912"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 471710.73700996983,
            "unit": "iter/sec",
            "range": "stddev: 1.652370644967651e-7",
            "extra": "mean: 2.119943265100757 usec\nrounds: 139665"
          }
        ]
      }
    ]
  }
}