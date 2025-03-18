window.BENCHMARK_DATA = {
  "lastUpdate": 1742315384093,
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
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3da062c12b7f9d84eb196a9f8169330a54d5e3fd",
          "message": "Merge pull request #157 from NCSU-High-Powered-Rocketry-Club/sim-config-pelicanator\n\nCreate Simulation config for Pelicanator",
          "timestamp": "2025-02-22T05:39:00-05:00",
          "tree_id": "dda99950413aab9bc6b4d7eaf4f48f6183baf75a",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/3da062c12b7f9d84eb196a9f8169330a54d5e3fd"
        },
        "date": 1740220784405,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1103.0899222494002,
            "unit": "iter/sec",
            "range": "stddev: 0.0008388784675033362",
            "extra": "mean: 906.5444075137763 usec\nrounds: 346"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3157.7265769574838,
            "unit": "iter/sec",
            "range": "stddev: 0.000015867688401630106",
            "extra": "mean: 316.68353026420505 usec\nrounds: 1586"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 106582.5351521931,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013388268526056967",
            "extra": "mean: 9.382400208177291 usec\nrounds: 4795"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 492562.5580019611,
            "unit": "iter/sec",
            "range": "stddev: 4.158193926977467e-7",
            "extra": "mean: 2.030198974230637 usec\nrounds: 45046"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "04fc6c797f8a7ddc84e7510b57907f9a55054294",
          "message": "Merge pull request #158 from NCSU-High-Powered-Rocketry-Club/refine-code\n\nSwitch to Pelicanator Launch Config",
          "timestamp": "2025-02-22T06:12:29-05:00",
          "tree_id": "350e74f882240536fb95075716ef715e3252f53c",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/04fc6c797f8a7ddc84e7510b57907f9a55054294"
        },
        "date": 1740222810537,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1073.0947058595268,
            "unit": "iter/sec",
            "range": "stddev: 0.0008571692147807295",
            "extra": "mean: 931.8841986076342 usec\nrounds: 428"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3214.5965925763057,
            "unit": "iter/sec",
            "range": "stddev: 0.000017149464363004505",
            "extra": "mean: 311.08102407293353 usec\nrounds: 1786"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 160055.70370750097,
            "unit": "iter/sec",
            "range": "stddev: 0.000003941746134295204",
            "extra": "mean: 6.247824831206782 usec\nrounds: 9568"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 503475.0287458594,
            "unit": "iter/sec",
            "range": "stddev: 3.655157136421399e-7",
            "extra": "mean: 1.9861958248276361 usec\nrounds: 75302"
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
          "id": "ef5d76162b2673a30c4eb36776a5f8cb739a4e9e",
          "message": "Merge pull request #169 from NCSU-High-Powered-Rocketry-Club/pre-commit-ci-update-config\n\n[pre-commit.ci] pre-commit autoupdate",
          "timestamp": "2025-03-03T13:11:47-05:00",
          "tree_id": "a5c39138f85c75d3e64105485944695728ad49d9",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/ef5d76162b2673a30c4eb36776a5f8cb739a4e9e"
        },
        "date": 1741025561974,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 878.9274725114008,
            "unit": "iter/sec",
            "range": "stddev: 0.0008505949362228935",
            "extra": "mean: 1.1377503050879192 msec\nrounds: 354"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3190.6089067341686,
            "unit": "iter/sec",
            "range": "stddev: 0.000016972772143546255",
            "extra": "mean: 313.4197982991203 usec\nrounds: 1532"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 133810.02016171516,
            "unit": "iter/sec",
            "range": "stddev: 0.000004955762405110816",
            "extra": "mean: 7.473281887196916 usec\nrounds: 7017"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 495707.73847784055,
            "unit": "iter/sec",
            "range": "stddev: 4.856897482457075e-7",
            "extra": "mean: 2.0173177103724047 usec\nrounds: 45211"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "6f9be4181722114b69f13f99c0abd8096ed9706b",
          "message": "Merge pull request #164 from NCSU-High-Powered-Rocketry-Club/pelicanator-data\n\nAdd pelicanator launch and fix mock",
          "timestamp": "2025-03-04T00:18:36-05:00",
          "tree_id": "555833db82c240a048dfe44fbcac354e540e8fe4",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/6f9be4181722114b69f13f99c0abd8096ed9706b"
        },
        "date": 1741065564340,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1083.181153113098,
            "unit": "iter/sec",
            "range": "stddev: 0.0008556252689326917",
            "extra": "mean: 923.2066096478576 usec\nrounds: 456"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestIMUDataProcessor::test_benchmark_data_processor_update",
            "value": 3177.7892140769545,
            "unit": "iter/sec",
            "range": "stddev: 0.00001470326360787043",
            "extra": "mean: 314.68418218873836 usec\nrounds: 1718"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 158282.7727186124,
            "unit": "iter/sec",
            "range": "stddev: 0.00000473066903305692",
            "extra": "mean: 6.317806940226859 usec\nrounds: 9510"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 499072.32491764316,
            "unit": "iter/sec",
            "range": "stddev: 4.2699725022824036e-7",
            "extra": "mean: 2.0037175977750716 usec\nrounds: 72464"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "9987674881c697015c8fb1a0fd6e28ab3dfe003b",
          "message": "Merge pull request #166 from NCSU-High-Powered-Rocketry-Club/read-metadata\n\n`MockIMU` upgrades, `--mock-servo` & `--mock-camera` for `uv run real`",
          "timestamp": "2025-03-04T17:09:59-05:00",
          "tree_id": "d50899ceb665a628191d68e8c8fd5108f04a950c",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/9987674881c697015c8fb1a0fd6e28ab3dfe003b"
        },
        "date": 1741126251581,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1041.6409816346725,
            "unit": "iter/sec",
            "range": "stddev: 0.0008794173126234665",
            "extra": "mean: 960.0236719091789 usec\nrounds: 445"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3190.734471313448,
            "unit": "iter/sec",
            "range": "stddev: 0.000013433714862846107",
            "extra": "mean: 313.4074643285361 usec\nrounds: 1682"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 148654.33487782598,
            "unit": "iter/sec",
            "range": "stddev: 0.000005274317572636756",
            "extra": "mean: 6.727015400000723 usec\nrounds: 8961"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 484446.77222023293,
            "unit": "iter/sec",
            "range": "stddev: 3.592747462087006e-7",
            "extra": "mean: 2.0642102648697036 usec\nrounds: 52743"
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
          "id": "5f7b9ab30b1d1db4b89068cf7a258079a6193273",
          "message": "Merge pull request #172 from NCSU-High-Powered-Rocketry-Club/fsync\n\nUse `os.fsync()` to guarantee disk write",
          "timestamp": "2025-03-05T19:57:35-05:00",
          "tree_id": "787786ffe53c2a5aeb58f997f1e16ab02dd8aa82",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/5f7b9ab30b1d1db4b89068cf7a258079a6193273"
        },
        "date": 1741222713339,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 1005.4830332074724,
            "unit": "iter/sec",
            "range": "stddev: 0.0008761587026171951",
            "extra": "mean: 994.5468665045678 usec\nrounds: 412"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3072.619541919852,
            "unit": "iter/sec",
            "range": "stddev: 0.00006386368849271466",
            "extra": "mean: 325.45519754625207 usec\nrounds: 1630"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 140191.18175826743,
            "unit": "iter/sec",
            "range": "stddev: 0.000005748534770977718",
            "extra": "mean: 7.1331162734922 usec\nrounds: 8179"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 510710.1167041423,
            "unit": "iter/sec",
            "range": "stddev: 3.9449257968490784e-7",
            "extra": "mean: 1.958057941858447 usec\nrounds: 52967"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "99681bf5ac34eee73e7bbcd102f8003d4549cf86",
          "message": "Merge pull request #173 from NCSU-High-Powered-Rocketry-Club/quad_fit\n\nAdded altitude and vel fix for when airbrakes deploy",
          "timestamp": "2025-03-05T22:55:54-05:00",
          "tree_id": "bcccacd5e2a28e1a32d56ea41de51f46bfe5782a",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/99681bf5ac34eee73e7bbcd102f8003d4549cf86"
        },
        "date": 1741233405186,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 901.3441072631795,
            "unit": "iter/sec",
            "range": "stddev: 0.0008801279571064651",
            "extra": "mean: 1.1094541939552665 msec\nrounds: 397"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3281.990051870823,
            "unit": "iter/sec",
            "range": "stddev: 0.00001331802912167797",
            "extra": "mean: 304.6931843775617 usec\nrounds: 1741"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 150799.05485699535,
            "unit": "iter/sec",
            "range": "stddev: 0.000024453989336704748",
            "extra": "mean: 6.63134129685569 usec\nrounds: 8916"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 513974.4155868291,
            "unit": "iter/sec",
            "range": "stddev: 3.4636735000422433e-7",
            "extra": "mean: 1.9456221354097019 usec\nrounds: 72047"
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
          "id": "f7ddfef4a566b1dab3de968adf15e69fd2068f06",
          "message": "Merge pull request #175 from NCSU-High-Powered-Rocketry-Club/revert-173-quad_fit\n\nRevert \"Added altitude and vel fix for when airbrakes deploy\"",
          "timestamp": "2025-03-07T22:10:17-05:00",
          "tree_id": "787786ffe53c2a5aeb58f997f1e16ab02dd8aa82",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/f7ddfef4a566b1dab3de968adf15e69fd2068f06"
        },
        "date": 1741403468403,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 967.7020125027907,
            "unit": "iter/sec",
            "range": "stddev: 0.0008966431587480946",
            "extra": "mean: 1.0333759639640268 msec\nrounds: 444"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 3158.6466572292893,
            "unit": "iter/sec",
            "range": "stddev: 0.00003265561389456225",
            "extra": "mean: 316.59128371046825 usec\nrounds: 1639"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 152257.75547148346,
            "unit": "iter/sec",
            "range": "stddev: 0.000005231608728591946",
            "extra": "mean: 6.567809941131643 usec\nrounds: 8571"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 507183.68393679353,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010730160077635124",
            "extra": "mean: 1.9716722593241434 usec\nrounds: 58824"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "85963782+JacksonElia@users.noreply.github.com",
            "name": "Jack",
            "username": "JacksonElia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "c938a350cb32069aad78f797fcc47586a8888dd8",
          "message": "Merge pull request #177 from NCSU-High-Powered-Rocketry-Club/pelicanator-data-2\n\nAdd Pelicanator launch 2 data",
          "timestamp": "2025-03-18T12:28:38-04:00",
          "tree_id": "669adf5197b347b2319e7575fa112adbdacb8fa7",
          "url": "https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/commit/c938a350cb32069aad78f797fcc47586a8888dd8"
        },
        "date": 1742315371721,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_airbrakes.py::TestAirbrakesContext::test_benchmark_airbrakes_update",
            "value": 595.4674750129583,
            "unit": "iter/sec",
            "range": "stddev: 0.0006700863970411137",
            "extra": "mean: 1.6793528479086761 msec\nrounds: 526"
          },
          {
            "name": "tests/test_components/test_data_processor.py::TestDataProcessor::test_benchmark_data_processor_update",
            "value": 6392.423970477781,
            "unit": "iter/sec",
            "range": "stddev: 0.000006048727187931348",
            "extra": "mean: 156.43518086696278 usec\nrounds: 2676"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_log_method",
            "value": 273621.7606863922,
            "unit": "iter/sec",
            "range": "stddev: 0.000014405657348601353",
            "extra": "mean: 3.6546800864502003 usec\nrounds: 10656"
          },
          {
            "name": "tests/test_components/test_logger.py::TestLogger::test_benchmark_prepare_logger_packets",
            "value": 807319.3482714578,
            "unit": "iter/sec",
            "range": "stddev: 1.329777112034981e-7",
            "extra": "mean: 1.2386672041752604 usec\nrounds: 120308"
          }
        ]
      }
    ]
  }
}