window.BENCHMARK_DATA = {
  "lastUpdate": 1740209389955,
  "repoUrl": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "130889585+wlsanderson@users.noreply.github.com",
            "name": "Will Sanderson",
            "username": "wlsanderson"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "46ad558e6d9afbb0f72ae273fe2aa20d651ed33d",
          "message": "Merge pull request #146 from NCSU-High-Powered-Rocketry-Club/imu-fix\n\nOptimize Reading IMU Data",
          "timestamp": "2025-02-18T17:10:51-05:00",
          "tree_id": "e031cf87f5b5abe3802e76f925143dd4bf058c03",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/46ad558e6d9afbb0f72ae273fe2aa20d651ed33d"
        },
        "date": 1739916726405,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1634.5392849932116,
            "unit": "iter/sec",
            "range": "stddev: 0.0003956507260947544",
            "extra": "mean: 611.7931879527466 usec\nrounds: 415"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3154.4962838987026,
            "unit": "iter/sec",
            "range": "stddev: 0.000023510434323909205",
            "extra": "mean: 317.0078231203622 usec\nrounds: 1436"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 131091.84222668316,
            "unit": "iter/sec",
            "range": "stddev: 0.000002860995215098576",
            "extra": "mean: 7.628239736465114 usec\nrounds: 6674"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 500906.4574477383,
            "unit": "iter/sec",
            "range": "stddev: 4.092191017985922e-7",
            "extra": "mean: 1.9963807316345774 usec\nrounds: 54348"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "130889585+wlsanderson@users.noreply.github.com",
            "name": "Will Sanderson",
            "username": "wlsanderson"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3fdbe7d1472162301221ca9765d26a32868f1fcb",
          "message": "Merge pull request #155 from NCSU-High-Powered-Rocketry-Club/bye-windows\n\nRemove Windows support",
          "timestamp": "2025-02-18T17:21:53-05:00",
          "tree_id": "b3e35ce68550ead00891af26415bfee99460efea",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/3fdbe7d1472162301221ca9765d26a32868f1fcb"
        },
        "date": 1739917386119,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1640.2816138711103,
            "unit": "iter/sec",
            "range": "stddev: 0.00040622503346285013",
            "extra": "mean: 609.6514107964498 usec\nrounds: 426"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3274.663830417982,
            "unit": "iter/sec",
            "range": "stddev: 0.000013007491701118867",
            "extra": "mean: 305.3748573246246 usec\nrounds: 1577"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151070.2889051809,
            "unit": "iter/sec",
            "range": "stddev: 0.000004307103956464937",
            "extra": "mean: 6.619435279081573 usec\nrounds: 8498"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 508927.1680983904,
            "unit": "iter/sec",
            "range": "stddev: 3.8957026436144565e-7",
            "extra": "mean: 1.9649176988065038 usec\nrounds: 45127"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "37377066+harshil21@users.noreply.github.com",
            "name": "Harshil",
            "username": "harshil21"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "8bd851b18e3f2f9f5616e3ca5fd0e4bd51cf888f",
          "message": "Merge pull request #153 from NCSU-High-Powered-Rocketry-Club/update-docs\n\nMeticulous Refining of Comments & Docs",
          "timestamp": "2025-02-19T13:08:51-05:00",
          "tree_id": "1bbcaf632387600c883fe6bf47ffb9837b1c5465",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/8bd851b18e3f2f9f5616e3ca5fd0e4bd51cf888f"
        },
        "date": 1739988577440,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1619.6114428260498,
            "unit": "iter/sec",
            "range": "stddev: 0.00040619573138856444",
            "extra": "mean: 617.4320417587976 usec\nrounds: 455"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3257.0880298235365,
            "unit": "iter/sec",
            "range": "stddev: 0.000013401168197762592",
            "extra": "mean: 307.02271195727496 usec\nrounds: 1656"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 157647.68136598033,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033895231809509",
            "extra": "mean: 6.343258532794353 usec\nrounds: 8904"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 513722.8405078519,
            "unit": "iter/sec",
            "range": "stddev: 6.909606551051247e-7",
            "extra": "mean: 1.9465749255209839 usec\nrounds: 55929"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "37377066+harshil21@users.noreply.github.com",
            "name": "Harshil",
            "username": "harshil21"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "d3c05e6ba42c5071a9ed0a1dcc3c5017e73c6aa8",
          "message": "Add legacy launch data (#143)\n\n* Add legacy launch 1 data and adjust tests\n\n* Add legacy launch 2 data\n\n---------\n\nCo-authored-by: Jack <85963782+JacksonElia@users.noreply.github.com>",
          "timestamp": "2025-02-22T00:56:03-05:00",
          "tree_id": "90a7e79d1bfe94b17480e0fe179fdb1e8531388f",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/d3c05e6ba42c5071a9ed0a1dcc3c5017e73c6aa8"
        },
        "date": 1740203815587,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1639.8274007822658,
            "unit": "iter/sec",
            "range": "stddev: 0.00041116381326649514",
            "extra": "mean: 609.8202771358489 usec\nrounds: 433"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3216.774188861653,
            "unit": "iter/sec",
            "range": "stddev: 0.000013878430726551998",
            "extra": "mean: 310.87043767715585 usec\nrounds: 1757"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 141980.0762995924,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034162748204663903",
            "extra": "mean: 7.043241742523778 usec\nrounds: 7599"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 505647.1715009545,
            "unit": "iter/sec",
            "range": "stddev: 4.4174831604678536e-7",
            "extra": "mean: 1.9776635890825156 usec\nrounds: 47439"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "37377066+harshil21@users.noreply.github.com",
            "name": "Harshil",
            "username": "harshil21"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f54baf49e524e1550e5f0c5f01754eb5a6fc9a4b",
          "message": "Use 2 servos, new board, new logic (#156)\n\n* Use 2 servos, new board, new logic\n\n* new test script\n\n* Add MockServo class, rearrange stuff into `interfaces`\n\nNo tests yet, but mock works\n\n* Get tests working\n\n* Move dependency in pyproject\n\n* Try to fix arm64 tests\n\n* Skip testing test_main on arm64\n\n* Skip testing test_main on arm64 take 2\n\n* Skip testing test_main on arm64 take 3\n\n* Skip testing test_main on arm64 take 4\n\n* Skip testing test_main on arm64 take 5\n\n* Skip testing test_main on arm64 take 6\n\n* script change\n\n* Change a few constants\n\nCo-authored-by: Harshil <hoppingturtles@proton.me>\n\n* Run mock replay with real imu\n\n* Fix tests\n\n* Update some constants\n\n* Fix tests\n\n* Review: Change docstring\n\n* Actually fix tests\n\n---------\n\nCo-authored-by: dirtypi <dirtypi09@gmail.com>",
          "timestamp": "2025-02-22T02:28:31-05:00",
          "tree_id": "6ec7ec2df65ff83b38b8bb0f9d5f4124b5156ed7",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/f54baf49e524e1550e5f0c5f01754eb5a6fc9a4b"
        },
        "date": 1740209373809,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 955.7536936603351,
            "unit": "iter/sec",
            "range": "stddev: 0.0008718846348093477",
            "extra": "mean: 1.046294674698259 msec\nrounds: 415"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3272.911728448225,
            "unit": "iter/sec",
            "range": "stddev: 0.000012295621815999033",
            "extra": "mean: 305.53833496576664 usec\nrounds: 1633"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 151788.7049041803,
            "unit": "iter/sec",
            "range": "stddev: 0.000004563326896139129",
            "extra": "mean: 6.588105489346327 usec\nrounds: 8636"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 514598.70531568135,
            "unit": "iter/sec",
            "range": "stddev: 3.931585239725915e-7",
            "extra": "mean: 1.9432617876225486 usec\nrounds: 48356"
          }
        ]
      }
    ]
  }
}