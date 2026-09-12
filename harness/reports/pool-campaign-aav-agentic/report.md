# pool-campaign / aav-agentic:一次中断的零轮运行

## 一句话

**这份产物不是实验结果,是一次没跑起来的运行留下的现场。**
`n_rounds = 0`、`rounds = []`、`summary` 四个字段全是 `null`。
任何把它当作 agentic 策略在 AAV 上表现的引用都是错的。

## 证据

| 字段 | 值 |
|---|---|
| `dataset` | `aav[one_hot]` |
| `n_rounds` | **0** |
| `rounds` | **`[]`** |
| `summary.final_cum_top10_max` | **`null`** |
| `summary.final_cum_top10_mean` | **`null`** |
| `summary.final_cum_n_strong` | **`null`** |
| `summary.cum_top10_max_curve` | **`[]`** |
| 事件流 `pool_events_aav_agentic.jsonl` | 30 条 |

事件流里有 30 条记录而轮次是 0 —— 说明进程起来了、走到了准备阶段,
但一轮完整的「提名 → oracle → 回流」都没完成就结束了。

`pool_curve_aav_agentic.png` 是在空曲线上画出来的图,**没有可读的数据点**。

## 为什么保留它

保留的理由不是它有结果,而是:

1. **不删有记录的失败**。删掉它,下一个人就会重新做一遍同样没做成的事,而且不知道
   前面有人试过、卡在哪。
2. **它是「静默零轮」这一类缺陷的现场**。同一时期 `evolution/campaign.py` 的 agent
   策略也在静默跑 0 轮而不报错(根因见 fact `F-6306819A`:`run_pipeline` 把「已测池」
   当成了「可测空间」,提名与池子求交集必然为空)。本目录是同一类故障在 pool-campaign
   这条线上的留痕。
3. **它是 manifest 校验的一个真实样本**:三个文件的 SHA-256 都在 `manifest.json` 里,
   可独立重算。

## 引用规则

- **不得**从这里取任何数字。没有数字可取。
- 若要在报告里提及,只能作为「失败案例」或「工程缺陷现场」引用,
  并且必须写明 `n_rounds = 0`。
- AAV 上真正可引用的 agentic 结果在 `harness/reports/agentic-v0.1` 至 `agentic-v0.7`,
  知识增强对照在 `harness/reports/knowledge-ablation/`。

## 校验

```bash
python3 -c "
import json;d=json.load(open('harness/reports/pool-campaign-aav-agentic/pool_metrics_aav_agentic.json'))
print(d['n_rounds'], d['rounds'], d['summary'])"
# 期望输出:0 [] {'final_cum_top10_max': None, ...}
```

`manifest.json` 里三个 SHA-256 可用 `shasum -a 256 <文件>` 逐个重算比对。
