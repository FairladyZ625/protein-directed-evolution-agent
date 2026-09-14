# Facts

Managed by `ha fact record`; hand edits are rejected.

## Records

### F-CD7724CF

- Statement: 受控交付 PDF harness/final-report/report.pdf 与 reports/final-report-v0.7/scientific_report_v0.7_two_column.pdf 的 sha256 同为 30b9173739beaea3ef0efd1746cd186cfacba9ae15203ad450ab4f7b2cb6c321(同一份文件),pdfinfo 与独立正则计数双仪器一致实测 44 页;README.md:11 入口指向的 v0.6 PDF 为 25 页;仓内唯一 4 页的 reports/report.pdf 是另一文件(sha256 e3180e58…)且 README 已不再链接它。试题 AI4S-assignment.md:72 明文要求 PDF 3—5 页,故无任何当前入口满足该要求:H32(提交 PDF)应判已交付、H33(3–5 页)应由已交付翻为未达标。
- Evidence source: shasum -a 256 harness/final-report/report.pdf reports/final-report-v0.7/scientific_report_v0.7_two_column.pdf; pdfinfo 三份 PDF; lab/context/research/AI4S-assignment.md:72
- Observed at: 2026-09-14T11:26:21.956Z
- Confidence: high
- State: standing

