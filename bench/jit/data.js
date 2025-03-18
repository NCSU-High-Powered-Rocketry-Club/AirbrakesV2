window.BENCHMARK_DATA = {
  "lastUpdate": 1742260520306,
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
          "id": "ad4c371f2aedd92cf007ebebd77f822e3c2a4b03",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/ad4c371f2aedd92cf007ebebd77f822e3c2a4b03"
        },
        "date": 1742176006581,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1082.5340654747702,
            "unit": "iter/sec",
            "range": "stddev: 0.0008772834888924691",
            "extra": "mean: 923.7584588725409 usec\nrounds: 462"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3097.7585084303428,
            "unit": "iter/sec",
            "range": "stddev: 0.000019329285216953893",
            "extra": "mean: 322.8140596752674 usec\nrounds: 1793"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 150219.12316761827,
            "unit": "iter/sec",
            "range": "stddev: 0.000018050594121922962",
            "extra": "mean: 6.656942065120265 usec\nrounds: 9528"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 496306.3331787896,
            "unit": "iter/sec",
            "range": "stddev: 5.714657345752729e-7",
            "extra": "mean: 2.014884624975679 usec\nrounds: 85911"
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
          "id": "f744db60328b585b5ce9fb49a94ca3d023c1213d",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/f744db60328b585b5ce9fb49a94ca3d023c1213d"
        },
        "date": 1742178375794,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 594.0084364890721,
            "unit": "iter/sec",
            "range": "stddev: 0.0006664493912771363",
            "extra": "mean: 1.6834777733302395 msec\nrounds: 525"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6474.602778573267,
            "unit": "iter/sec",
            "range": "stddev: 0.000005450163821754766",
            "extra": "mean: 154.4496294520725 usec\nrounds: 2723"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 299946.0761713967,
            "unit": "iter/sec",
            "range": "stddev: 0.000002871867820171042",
            "extra": "mean: 3.3339325946993714 usec\nrounds: 11824"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 800286.0857767622,
            "unit": "iter/sec",
            "range": "stddev: 1.163891396591175e-7",
            "extra": "mean: 1.2495531507703204 usec\nrounds: 117261"
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
          "id": "ee6f38bbc5a98685b14eaf0028ccb10126adfc69",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/ee6f38bbc5a98685b14eaf0028ccb10126adfc69"
        },
        "date": 1742259769159,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 576.933259968302,
            "unit": "iter/sec",
            "range": "stddev: 0.0006119887733850784",
            "extra": "mean: 1.7333027394796798 msec\nrounds: 499"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6375.880871639248,
            "unit": "iter/sec",
            "range": "stddev: 0.000006134582178829435",
            "extra": "mean: 156.84107343475173 usec\nrounds: 2492"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 282448.5189367933,
            "unit": "iter/sec",
            "range": "stddev: 0.000014030135643758098",
            "extra": "mean: 3.540468202008102 usec\nrounds: 11290"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 808543.7555006882,
            "unit": "iter/sec",
            "range": "stddev: 1.3170052665645982e-7",
            "extra": "mean: 1.2367914453569098 usec\nrounds: 109650"
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
          "id": "4976e0136b6d7066c97b28ff6e87abe91cecadcf",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/4976e0136b6d7066c97b28ff6e87abe91cecadcf"
        },
        "date": 1742260065149,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 628.1955048942118,
            "unit": "iter/sec",
            "range": "stddev: 0.0007481072392178606",
            "extra": "mean: 1.5918611200002142 msec\nrounds: 525"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6420.484264714413,
            "unit": "iter/sec",
            "range": "stddev: 0.000005374722102345115",
            "extra": "mean: 155.7514914405729 usec\nrounds: 2979"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 286293.09098508244,
            "unit": "iter/sec",
            "range": "stddev: 0.000002915438259244268",
            "extra": "mean: 3.4929239701844774 usec\nrounds: 10509"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 812162.4359802371,
            "unit": "iter/sec",
            "range": "stddev: 1.4758314766642147e-7",
            "extra": "mean: 1.2312807828806476 usec\nrounds: 120773"
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
          "id": "149e81b02ac99724cb77259880c5385c26b2113e",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/149e81b02ac99724cb77259880c5385c26b2113e"
        },
        "date": 1742260316889,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1072.5800554508457,
            "unit": "iter/sec",
            "range": "stddev: 0.0008658172528226131",
            "extra": "mean: 932.3313396683125 usec\nrounds: 421"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3161.4486683574028,
            "unit": "iter/sec",
            "range": "stddev: 0.00001860086952220565",
            "extra": "mean: 316.3106869356734 usec\nrounds: 1661"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 145882.10034935118,
            "unit": "iter/sec",
            "range": "stddev: 0.00000551403958669353",
            "extra": "mean: 6.8548505786881995 usec\nrounds: 8379"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 494382.9746274638,
            "unit": "iter/sec",
            "range": "stddev: 3.9153110968778934e-7",
            "extra": "mean: 2.022723377061149 usec\nrounds: 51760"
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
          "id": "149e81b02ac99724cb77259880c5385c26b2113e",
          "message": "Use JIT / LLVM 20 built Python for performance improvements",
          "timestamp": "2025-03-16T22:46:14Z",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/179/commits/149e81b02ac99724cb77259880c5385c26b2113e"
        },
        "date": 1742260508449,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 592.6819611029836,
            "unit": "iter/sec",
            "range": "stddev: 0.0006676370284171971",
            "extra": "mean: 1.6872455475766397 msec\nrounds: 557"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6454.178236559179,
            "unit": "iter/sec",
            "range": "stddev: 0.000003981560658982549",
            "extra": "mean: 154.93839236350487 usec\nrounds: 1519"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 273493.1964998981,
            "unit": "iter/sec",
            "range": "stddev: 0.000014769760681392438",
            "extra": "mean: 3.656398085209306 usec\nrounds: 10445"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 811525.176125022,
            "unit": "iter/sec",
            "range": "stddev: 1.2599802224443369e-7",
            "extra": "mean: 1.2322476608488386 usec\nrounds: 144823"
          }
        ]
      }
    ]
  }
}