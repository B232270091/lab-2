# Лаборатори 2 — Гүйцэтгэлийн хэмжүүрийг k6-аар хэмжих

F.CSA313 — Программ хангамжийн чанарын баталгаа ба тест, 2026.

## Ажиллуулах

Python 3 болон [Grafana k6](https://grafana.com/docs/k6/latest/set-up/install-k6/)
суулгасан орчинд дараах командуудыг ашиглана.

```bash
python server.py
# Өөр terminal нээнэ.
k6 run script.js
k6 run -e TARGET_URL=http://127.0.0.1:8000/slow --vus 5 --duration 1m script.js
k6 run -e TARGET_URL=http://127.0.0.1:8000/slow --vus 30 --duration 1m script.js
k6 run -e TARGET_URL=http://127.0.0.1:8000/slow --vus 100 --duration 1m script.js
k6 run -e TARGET_URL=http://127.0.0.1:8000/slow stages.js
```

`script.js` нь 5 VU, 30 секундийн үндсэн тест, `stages.js` нь
5 → 30 → 100 → 0 VU ачааллын өсөлт, бууралтыг туршина.
Локал `/slow` endpoint 100 ms ажиллаж, найман хүсэлтийг зэрэг боловсруулна.
`/fast` endpoint-д зориудын хүлээлт байхгүй.

Хэмжилтийн хүснэгтийн мөр бүрийг тогтмол VU-тэй тусдаа ажиллуулалтаас авна.
Stages-ийн нэгтгэсэн summary-г түвшин тус бүрийн p95 гэж ашиглахгүй.

## Хэмжилтийн орчин

2026-11-18, UTC+08:00; Windows 11 x64, Python 3.14.8.

```text
k6.exe v2.4.0 (commit/dd9395906d, go1.26.11, windows/amd64)
```

Бай: `http://127.0.0.1:8000/slow`. Нэг iteration тутам нэг GET хүсэлт,
дараа нь `sleep(1)` хийнэ. Туршилтуудыг давхцуулахгүйгээр дараалан ажиллуулсан.

## 5, 30, 100 VU-ийн харьцуулалт

Мөр бүр нэг минутын тусдаа ажиллуулалт. Latency-ийн нэгж ms,
throughput-ийн нэгж хүсэлт/сек. Throughput-ийг k6-ийн `http_reqs` rate-ээс авсан.

| VU | avg ms | p90 ms | p95 ms | p99 ms | Нийт хүсэлт | Throughput req/s | Error rate | Бүтэн гаралт |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5 | 101.11 | 101.63 | 101.81 | 102.26 | 275 | 4.538937 | 0.00% | [run-05vu.txt](results/run-05vu.txt) |
| 30 | 103.76 | 101.84 | 102.28 | 203.63 | 1650 | 27.098274 | 0.00% | [run-30vu.txt](results/run-30vu.txt) |
| 100 | 266.83 | 308.13 | 309.75 | 710.15 | 4781 | 78.104864 | 0.00% | [run-100vu.txt](results/run-100vu.txt) |

## Baseline ба SLO

5 VU, 30 секундийн baseline-ийн p95 = **101.865810 ms**
([текст](results/baseline-05vu.txt), [JSON](results/baseline-05vu.json)).
`ceil(101.865810 × 1.5) = 153 ms` тул `p(95)<153` босго сонгосон.
Baseline-аас 50% хэлбэлзлийг зөвшөөрөх боловч хэт ачааллын үед latency
огцом өссөнийг илрүүлэхийн тулд энэ нөөцийг авсан.

`thresholds.js` нь хадгалсан baseline JSON-оос босгыг тооцно;
`stages` агуулаагүй бөгөөд 30 VU, нэг минут ажиллана.

| Туршилт | Latency босго | Бодит p95 ms | Error rate | Exit code | Үр дүн |
| --- | --- | ---: | ---: | ---: | --- |
| [Ердийн SLO](results/run-slo-pass.txt) | p95 < 153 ms | 102.72 | 0.00% | 0 | PASS |
| [Зориудын хатуу SLO](results/run-slo-fail.txt) | p95 < 50 ms | 102.74 | 0.00% | 99 | FAIL |

Хоёуланд нь `http_req_failed: rate<0.01`, `checks: rate==1` шалгасан.
50 ms нь серверийн зориудын 100 ms боловсруулалтаас бага тул latency
threshold унасан ч HTTP болон status check амжилттай хэвээр байна.
