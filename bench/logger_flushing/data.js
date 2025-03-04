window.BENCHMARK_DATA = {
  "lastUpdate": 1741104991611,
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
          "id": "51a98251cdd1c6439b7249e8810b853dd9224fcb",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/51a98251cdd1c6439b7249e8810b853dd9224fcb"
        },
        "date": 1740345851636,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 984.8632822099753,
            "unit": "iter/sec",
            "range": "stddev: 0.000864534862962819",
            "extra": "mean: 1.015369359446581 msec\nrounds: 434"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3106.5294135173185,
            "unit": "iter/sec",
            "range": "stddev: 0.00001783503328814815",
            "extra": "mean: 321.9026337393554 usec\nrounds: 1559"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 131503.0343418168,
            "unit": "iter/sec",
            "range": "stddev: 0.000004423099756546365",
            "extra": "mean: 7.604387267602456 usec\nrounds: 6990"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503455.00051847094,
            "unit": "iter/sec",
            "range": "stddev: 3.7311162671948827e-7",
            "extra": "mean: 1.986274838804211 usec\nrounds: 62815"
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
          "id": "bdaba21282c803117642c88abd5e26fc38128808",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-02-22T11:12:33Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/bdaba21282c803117642c88abd5e26fc38128808"
        },
        "date": 1740951471869,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1037.0518687569725,
            "unit": "iter/sec",
            "range": "stddev: 0.0008396332975129279",
            "extra": "mean: 964.2719232535751 usec\nrounds: 430"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3265.55774814378,
            "unit": "iter/sec",
            "range": "stddev: 0.00001532281861168563",
            "extra": "mean: 306.22640208044817 usec\nrounds: 1634"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151617.7368810659,
            "unit": "iter/sec",
            "range": "stddev: 0.000004300289750782662",
            "extra": "mean: 6.5955344049518025 usec\nrounds: 8458"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 511955.346187613,
            "unit": "iter/sec",
            "range": "stddev: 4.186621559184496e-7",
            "extra": "mean: 1.9532953556334902 usec\nrounds: 49801"
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
          "id": "d5c248d7e7cb538964c669f4b4ba6698b60cb581",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-03-03T18:11:51Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/d5c248d7e7cb538964c669f4b4ba6698b60cb581"
        },
        "date": 1741039525166,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1020.3115058511072,
            "unit": "iter/sec",
            "range": "stddev: 0.0009041785627826705",
            "extra": "mean: 980.0928385746626 usec\nrounds: 477"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3266.473553244376,
            "unit": "iter/sec",
            "range": "stddev: 0.000012114403397960541",
            "extra": "mean: 306.14054689246296 usec\nrounds: 1770"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 157418.9762701695,
            "unit": "iter/sec",
            "range": "stddev: 0.000004282208167076774",
            "extra": "mean: 6.35247429308494 usec\nrounds: 9161"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 510736.6375044614,
            "unit": "iter/sec",
            "range": "stddev: 3.4752611179151837e-7",
            "extra": "mean: 1.957956266631185 usec\nrounds: 62035"
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
          "id": "88bb2ba59ded679b0ef0184b503b508988a9eb25",
          "message": "Add Logger flushing and launch data",
          "timestamp": "2025-03-03T18:11:51Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/88bb2ba59ded679b0ef0184b503b508988a9eb25"
        },
        "date": 1741061762259,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 986.8972318936995,
            "unit": "iter/sec",
            "range": "stddev: 0.0008921516640621292",
            "extra": "mean: 1.0132767300209753 msec\nrounds: 463"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3236.071959130122,
            "unit": "iter/sec",
            "range": "stddev: 0.000011071338884285023",
            "extra": "mean: 309.01661416355114 usec\nrounds: 1638"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 144830.56574396085,
            "unit": "iter/sec",
            "range": "stddev: 0.000005365771268394316",
            "extra": "mean: 6.904619856058928 usec\nrounds: 8189"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 483309.61758820416,
            "unit": "iter/sec",
            "range": "stddev: 3.5608855921303177e-7",
            "extra": "mean: 2.0690670402756877 usec\nrounds: 64767"
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
          "id": "4588cff0e20e53c19bd83db25f36c7de04bb80fe",
          "message": "Add Logger flushing",
          "timestamp": "2025-03-04T05:18:40Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/4588cff0e20e53c19bd83db25f36c7de04bb80fe"
        },
        "date": 1741103182938,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1051.5274292400802,
            "unit": "iter/sec",
            "range": "stddev: 0.0008608371143204587",
            "extra": "mean: 950.997541474198 usec\nrounds: 434"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3050.8170438095667,
            "unit": "iter/sec",
            "range": "stddev: 0.00003494546613168484",
            "extra": "mean: 327.78104541834347 usec\nrounds: 1255"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 143873.60297109897,
            "unit": "iter/sec",
            "range": "stddev: 0.0000057645981854838925",
            "extra": "mean: 6.950545335275144 usec\nrounds: 8393"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 494913.8090811456,
            "unit": "iter/sec",
            "range": "stddev: 8.662203306666836e-7",
            "extra": "mean: 2.0205538452374054 usec\nrounds: 50608"
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
          "id": "72f5882f603cf9cf353bcdb3a23d876be53fc07d",
          "message": "Add Logger flushing",
          "timestamp": "2025-03-04T05:18:40Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/72f5882f603cf9cf353bcdb3a23d876be53fc07d"
        },
        "date": 1741103755693,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1053.1887650962854,
            "unit": "iter/sec",
            "range": "stddev: 0.0008901664727032894",
            "extra": "mean: 949.4974055373418 usec\nrounds: 434"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3256.398692725148,
            "unit": "iter/sec",
            "range": "stddev: 0.000015646991641049903",
            "extra": "mean: 307.08770465791474 usec\nrounds: 1588"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151494.66775293922,
            "unit": "iter/sec",
            "range": "stddev: 0.000005525070118730625",
            "extra": "mean: 6.600892393327149 usec\nrounds: 8243"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 514349.8880040065,
            "unit": "iter/sec",
            "range": "stddev: 4.474465461130469e-7",
            "extra": "mean: 1.9442018426029295 usec\nrounds: 52967"
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
          "id": "dd0a9335843850139e4ab8abe005515148cebdc2",
          "message": "Add Logger flushing",
          "timestamp": "2025-03-04T05:18:40Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/161/commits/dd0a9335843850139e4ab8abe005515148cebdc2"
        },
        "date": 1741104977709,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1028.6000177741537,
            "unit": "iter/sec",
            "range": "stddev: 0.0008859046429007563",
            "extra": "mean: 972.1952000000516 usec\nrounds: 460"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3179.9446148956845,
            "unit": "iter/sec",
            "range": "stddev: 0.000012326762137049637",
            "extra": "mean: 314.4708858499425 usec\nrounds: 1682"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151904.3304309824,
            "unit": "iter/sec",
            "range": "stddev: 0.0000050896674293194365",
            "extra": "mean: 6.583090799075996 usec\nrounds: 9075"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 488707.90687778266,
            "unit": "iter/sec",
            "range": "stddev: 3.632949291747253e-7",
            "extra": "mean: 2.0462120336638683 usec\nrounds: 57472"
          }
        ]
      }
    ]
  }
}