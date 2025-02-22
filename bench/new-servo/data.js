window.BENCHMARK_DATA = {
  "lastUpdate": 1740203120146,
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
          "id": "9c5c86471ba20a5d173b18b8b20d972a11f43bd9",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/9c5c86471ba20a5d173b18b8b20d972a11f43bd9"
        },
        "date": 1740121687252,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1621.5848632881593,
            "unit": "iter/sec",
            "range": "stddev: 0.00041319425558127546",
            "extra": "mean: 616.6806453608946 usec\nrounds: 485"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3287.558692668578,
            "unit": "iter/sec",
            "range": "stddev: 0.000010110327069913784",
            "extra": "mean: 304.17707894616467 usec\nrounds: 1672"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 143140.27849478376,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042202769578296385",
            "extra": "mean: 6.986153796231725 usec\nrounds: 7627"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 508872.4830106446,
            "unit": "iter/sec",
            "range": "stddev: 2.91171628306784e-7",
            "extra": "mean: 1.9651288552363753 usec\nrounds: 60828"
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
          "id": "d60e5735553e77160265ecd09ca438ea0b37f279",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/d60e5735553e77160265ecd09ca438ea0b37f279"
        },
        "date": 1740127192888,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1633.2366611391838,
            "unit": "iter/sec",
            "range": "stddev: 0.0004028672112464736",
            "extra": "mean: 612.2811370781374 usec\nrounds: 445"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3229.782813255825,
            "unit": "iter/sec",
            "range": "stddev: 0.000015572183771494136",
            "extra": "mean: 309.61834210515747 usec\nrounds: 1634"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 143407.45475752107,
            "unit": "iter/sec",
            "range": "stddev: 0.000004354288498349122",
            "extra": "mean: 6.973138193484007 usec\nrounds: 7750"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 507363.74341375596,
            "unit": "iter/sec",
            "range": "stddev: 3.8260568399761864e-7",
            "extra": "mean: 1.9709725280556722 usec\nrounds: 53764"
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
          "id": "08387f76f1d5b80b1ec1ae10a731bb4d4ae0c11e",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/08387f76f1d5b80b1ec1ae10a731bb4d4ae0c11e"
        },
        "date": 1740172481970,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1632.3594381477158,
            "unit": "iter/sec",
            "range": "stddev: 0.0004103085538057026",
            "extra": "mean: 612.6101743466061 usec\nrounds: 499"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3202.5190279709395,
            "unit": "iter/sec",
            "range": "stddev: 0.000014140471328524926",
            "extra": "mean: 312.25419467174333 usec\nrounds: 1726"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 158500.23477122278,
            "unit": "iter/sec",
            "range": "stddev: 0.000004136917711634618",
            "extra": "mean: 6.309138919846947 usec\nrounds: 9322"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 501311.46981192037,
            "unit": "iter/sec",
            "range": "stddev: 3.4817177387557997e-7",
            "extra": "mean: 1.9947678443806107 usec\nrounds: 67205"
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
          "id": "733bf42b5a3fe7c792d3ac3142eb138d3136aa30",
          "message": "Use 2 servos, new board, new logic",
          "timestamp": "2025-02-19T18:08:56Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/156/commits/733bf42b5a3fe7c792d3ac3142eb138d3136aa30"
        },
        "date": 1740203103275,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1617.891450388951,
            "unit": "iter/sec",
            "range": "stddev: 0.0004018615926368242",
            "extra": "mean: 618.088438355734 usec\nrounds: 438"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3115.880042609353,
            "unit": "iter/sec",
            "range": "stddev: 0.00003513565554959169",
            "extra": "mean: 320.9366170472221 usec\nrounds: 1619"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151725.28423885207,
            "unit": "iter/sec",
            "range": "stddev: 0.000004377420731244627",
            "extra": "mean: 6.590859295578974 usec\nrounds: 8429"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 499230.1296866886,
            "unit": "iter/sec",
            "range": "stddev: 6.698469823965011e-7",
            "extra": "mean: 2.0030842301677367 usec\nrounds: 39309"
          }
        ]
      }
    ]
  }
}