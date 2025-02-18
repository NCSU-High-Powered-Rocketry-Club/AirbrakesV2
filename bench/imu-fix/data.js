window.BENCHMARK_DATA = {
  "lastUpdate": 1739846808615,
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
          "id": "99b0c38ca167ab30522f8bb471f95b6807a0559e",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/99b0c38ca167ab30522f8bb471f95b6807a0559e"
        },
        "date": 1738461425182,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 9.928878056307784,
            "unit": "iter/sec",
            "range": "stddev: 0.0000887442639263093",
            "extra": "mean: 100.71631400132901 msec\nrounds: 10"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6429.4645666552515,
            "unit": "iter/sec",
            "range": "stddev: 0.000015302160838572258",
            "extra": "mean: 155.53394682136368 usec\nrounds: 2410"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 226962.74464358654,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024564909969509335",
            "extra": "mean: 4.406009460144488 usec\nrounds: 12148"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 480803.8457083877,
            "unit": "iter/sec",
            "range": "stddev: 1.5060977962691832e-7",
            "extra": "mean: 2.079850252708898 usec\nrounds: 114365"
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
          "id": "379a10f904e149fff4584f1c0c3391159f593fb3",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-01-29T02:23:30Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/379a10f904e149fff4584f1c0c3391159f593fb3"
        },
        "date": 1738461601035,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1347.3468969123426,
            "unit": "iter/sec",
            "range": "stddev: 0.00038247557587207356",
            "extra": "mean: 742.1993565960314 usec\nrounds: 519"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6494.644735103068,
            "unit": "iter/sec",
            "range": "stddev: 0.000005045415388564311",
            "extra": "mean: 153.9730101933174 usec\nrounds: 2808"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 228623.6510886759,
            "unit": "iter/sec",
            "range": "stddev: 0.000002406251368390881",
            "extra": "mean: 4.374000656704286 usec\nrounds: 12496"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 477577.5258723319,
            "unit": "iter/sec",
            "range": "stddev: 1.4671346715155365e-7",
            "extra": "mean: 2.0939008764564946 usec\nrounds: 122911"
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
          "id": "65c4ae9ce71370ee0c4a86ce1973b0aa295bd7de",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/65c4ae9ce71370ee0c4a86ce1973b0aa295bd7de"
        },
        "date": 1738807570113,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1440.8048636823044,
            "unit": "iter/sec",
            "range": "stddev: 0.0004009092338485216",
            "extra": "mean: 694.0565132770809 usec\nrounds: 528"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6404.903781986615,
            "unit": "iter/sec",
            "range": "stddev: 0.000007498763322058139",
            "extra": "mean: 156.13037042218127 usec\nrounds: 2759"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 231976.06302946177,
            "unit": "iter/sec",
            "range": "stddev: 0.000002239609746878835",
            "extra": "mean: 4.310789600188174 usec\nrounds: 13014"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 478605.2905417716,
            "unit": "iter/sec",
            "range": "stddev: 1.6398249714416532e-7",
            "extra": "mean: 2.089404400164528 usec\nrounds: 130328"
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
          "id": "2d85a6c6bf946636c5e6b4aa74388b9d376289f3",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/2d85a6c6bf946636c5e6b4aa74388b9d376289f3"
        },
        "date": 1739005237524,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1419.5206887836764,
            "unit": "iter/sec",
            "range": "stddev: 0.00039939757900807376",
            "extra": "mean: 704.4631387914853 usec\nrounds: 490"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6389.605987592634,
            "unit": "iter/sec",
            "range": "stddev: 0.000006087028584434881",
            "extra": "mean: 156.50417286164506 usec\nrounds: 2389"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 207660.61848751098,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027926125511772794",
            "extra": "mean: 4.81554956006327 usec\nrounds: 9260"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_log_dict",
            "value": 493701.50072856754,
            "unit": "iter/sec",
            "range": "stddev: 1.878242023559835e-7",
            "extra": "mean: 2.0255154147278778 usec\nrounds: 123153"
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
          "id": "38e28d9e59489f60704b7f3217a9aa43b7a525a3",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/38e28d9e59489f60704b7f3217a9aa43b7a525a3"
        },
        "date": 1739006300601,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1189.3135046829186,
            "unit": "iter/sec",
            "range": "stddev: 0.00032237364912245076",
            "extra": "mean: 840.8211931189738 usec\nrounds: 554"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6468.874094512378,
            "unit": "iter/sec",
            "range": "stddev: 0.000005095472584767788",
            "extra": "mean: 154.58640644255416 usec\nrounds: 2689"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 314040.1033227159,
            "unit": "iter/sec",
            "range": "stddev: 0.000002120339223236941",
            "extra": "mean: 3.184306683826217 usec\nrounds: 12971"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 800588.78010015,
            "unit": "iter/sec",
            "range": "stddev: 1.2538907751838197e-7",
            "extra": "mean: 1.2490807076698034 usec\nrounds: 134972"
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
          "id": "c7ba1afb8ab43bba35699964b901e037cb0dce3c",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/c7ba1afb8ab43bba35699964b901e037cb0dce3c"
        },
        "date": 1739308481670,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1610.7218426807606,
            "unit": "iter/sec",
            "range": "stddev: 0.0004351456580606443",
            "extra": "mean: 620.8396592770342 usec\nrounds: 584"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6450.446117427205,
            "unit": "iter/sec",
            "range": "stddev: 0.000004826225342382129",
            "extra": "mean: 155.02803709937123 usec\nrounds: 2803"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 321045.38245473406,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019854085323900626",
            "extra": "mean: 3.1148244287269744 usec\nrounds: 13721"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 801576.4479023041,
            "unit": "iter/sec",
            "range": "stddev: 1.4138101196032173e-7",
            "extra": "mean: 1.2475416444893845 usec\nrounds: 120540"
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
          "id": "6cec39a54d063d35e3ba859c9961efba43335543",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/6cec39a54d063d35e3ba859c9961efba43335543"
        },
        "date": 1739312489107,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1632.423433839268,
            "unit": "iter/sec",
            "range": "stddev: 0.0004349379098707416",
            "extra": "mean: 612.5861582666193 usec\nrounds: 556"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6489.006834650009,
            "unit": "iter/sec",
            "range": "stddev: 0.000004863751144765808",
            "extra": "mean: 154.1067879078503 usec\nrounds: 2796"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 302689.3816280805,
            "unit": "iter/sec",
            "range": "stddev: 0.000002088236958367331",
            "extra": "mean: 3.303716815638801 usec\nrounds: 12017"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 803040.8529947266,
            "unit": "iter/sec",
            "range": "stddev: 1.2335576525777706e-7",
            "extra": "mean: 1.2452666589386663 usec\nrounds: 116050"
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
          "id": "26040b3bcd7ccbbd03346ae8e2b606c6951bd23a",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/26040b3bcd7ccbbd03346ae8e2b606c6951bd23a"
        },
        "date": 1739325934267,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1554.6799482567221,
            "unit": "iter/sec",
            "range": "stddev: 0.0004214013840181749",
            "extra": "mean: 643.2192047767194 usec\nrounds: 503"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 6452.988651666663,
            "unit": "iter/sec",
            "range": "stddev: 0.000006560137061360157",
            "extra": "mean: 154.96695469032358 usec\nrounds: 2494"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 297952.46008222987,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022501213833275676",
            "extra": "mean: 3.3562401187223525 usec\nrounds: 11482"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 809376.1656989957,
            "unit": "iter/sec",
            "range": "stddev: 1.1227180414246342e-7",
            "extra": "mean: 1.2355194560694496 usec\nrounds: 94189"
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
          "id": "030256066cd07d3d36e5eb31861f6ae883e356ff",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/030256066cd07d3d36e5eb31861f6ae883e356ff"
        },
        "date": 1739756201322,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1601.279922650207,
            "unit": "iter/sec",
            "range": "stddev: 0.0004027158675201286",
            "extra": "mean: 624.5004298467344 usec\nrounds: 449"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 2977.8485611324863,
            "unit": "iter/sec",
            "range": "stddev: 0.00002037330565957939",
            "extra": "mean: 335.81291307160916 usec\nrounds: 1599"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 137534.409924951,
            "unit": "iter/sec",
            "range": "stddev: 0.000004438853538194096",
            "extra": "mean: 7.270907698994559 usec\nrounds: 8819"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 469890.05862242426,
            "unit": "iter/sec",
            "range": "stddev: 4.1175699134404326e-7",
            "extra": "mean: 2.1281573884148517 usec\nrounds: 53079"
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
          "id": "b8505754a09877ef8daa6d99999b1d509469f8ac",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/b8505754a09877ef8daa6d99999b1d509469f8ac"
        },
        "date": 1739757474602,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1631.8379859056845,
            "unit": "iter/sec",
            "range": "stddev: 0.00039329798645019163",
            "extra": "mean: 612.8059333322794 usec\nrounds: 435"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3175.606695663779,
            "unit": "iter/sec",
            "range": "stddev: 0.00002617939854538017",
            "extra": "mean: 314.9004570891849 usec\nrounds: 1608"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 156967.7898458026,
            "unit": "iter/sec",
            "range": "stddev: 0.000003889534527130373",
            "extra": "mean: 6.370733772720828 usec\nrounds: 9413"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 485878.45978627645,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012539251431767877",
            "extra": "mean: 2.0581278709903508 usec\nrounds: 44803"
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
          "id": "46260353d461b6cd814f439c8e039eb7fe603742",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/46260353d461b6cd814f439c8e039eb7fe603742"
        },
        "date": 1739768839512,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1620.212709247249,
            "unit": "iter/sec",
            "range": "stddev: 0.000405188956020545",
            "extra": "mean: 617.2029106379496 usec\nrounds: 470"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3236.0249492246994,
            "unit": "iter/sec",
            "range": "stddev: 0.000011875372603294216",
            "extra": "mean: 309.0211032642329 usec\nrounds: 1685"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 158851.96498914302,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035762184478691344",
            "extra": "mean: 6.295169216624714 usec\nrounds: 9739"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 505526.6835744185,
            "unit": "iter/sec",
            "range": "stddev: 3.6646375595055994e-7",
            "extra": "mean: 1.9781349481481727 usec\nrounds: 74851"
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
          "id": "ffeb7c206f45cf3c9663d0f319b5865c1f9b0951",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/ffeb7c206f45cf3c9663d0f319b5865c1f9b0951"
        },
        "date": 1739846507174,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1625.6943361044005,
            "unit": "iter/sec",
            "range": "stddev: 0.00040816563788623986",
            "extra": "mean: 615.1217838380788 usec\nrounds: 495"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3173.005445139313,
            "unit": "iter/sec",
            "range": "stddev: 0.000016658954253071312",
            "extra": "mean: 315.15861453433286 usec\nrounds: 1720"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 156343.75965351943,
            "unit": "iter/sec",
            "range": "stddev: 0.000003713210727398714",
            "extra": "mean: 6.396161907684361 usec\nrounds: 9209"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 500367.6097331022,
            "unit": "iter/sec",
            "range": "stddev: 5.197313920032328e-7",
            "extra": "mean: 1.9985306413686597 usec\nrounds: 51760"
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
          "id": "1f2e423db0d03e19661c4e8f9d286f2b008dfd78",
          "message": "Optimize Reading IMU Data",
          "timestamp": "2025-02-04T20:23:44Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/146/commits/1f2e423db0d03e19661c4e8f9d286f2b008dfd78"
        },
        "date": 1739846792734,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1640.586465769403,
            "unit": "iter/sec",
            "range": "stddev: 0.0003987531331986348",
            "extra": "mean: 609.5381260694598 usec\nrounds: 468"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3254.1080961762946,
            "unit": "iter/sec",
            "range": "stddev: 0.000013506819826272769",
            "extra": "mean: 307.3038665110847 usec\nrounds: 1708"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 133949.77675166514,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028980295700052287",
            "extra": "mean: 7.465484633497673 usec\nrounds: 6768"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 517096.272982435,
            "unit": "iter/sec",
            "range": "stddev: 3.3464063615444107e-7",
            "extra": "mean: 1.933875860741252 usec\nrounds: 61125"
          }
        ]
      }
    ]
  }
}