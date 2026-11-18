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
