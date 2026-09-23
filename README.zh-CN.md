<p align="center"><img src="assets/hero.svg" alt="Jev 决策通过多叉区间树转化为数值输出" width="100%"></p>

<h1 align="center">A simple algorithm that turns Jev decisions into numerical outputs.</h1>
<p align="center"><strong>一个简单算法，把 Jev 的离散决策变成数值输出。</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="#实测结果">实测结果</a> · <a href="#快速开始">快速开始</a> · <a href="artifacts/metrics.json">可核对的指标</a></p>

**Jev 擅长结构化决策。我们利用这种能力，加上多叉数值决策树，构建一个可指定范围与精度的数值输出接口。** 每次只问“答案落在哪个区间”，再在选中的区间中继续细分。不训练模型，也不添加回归头。

## 输入什么，输出什么？

| 输入问题 | 数值输出 |
|---|---:|
| **1 + 1 等于多少？** | **`2.00`** |
| **一只股票现在 10 元，上涨 1 元后，价格是多少？** | **`11.00`** |
| **一只股票现在 10.50 元，上涨 1.25 元后，价格是多少？** | **`11.75`** |

以上是**实际调用结果**，不是预设的期望答案。测试使用英文问题，表中为中文翻译。三个例子统一在 `[0,100)` 上十叉细分，分辨率 `0.01`，每题四次 Choice 调用。**输入只包含题目，没有提供答案。** Jev 负责选择区间，解码器返回数值的十进制字符串及最终区间。

```python
from jev_numeric import JevClient, decode_number

with JevClient() as client:
    result = decode_number(
        client,
        state={"question": "A stock costs 10 yuan. It rises by 1 yuan. What is its new price in yuan?"},
        target="the numerical answer to the question, in the stated units",
        lower="0", upper="100", resolution="0.01", branching=10,
    )

print(result["value"])  # 实测输出：11.00
# 所选区间：[10,20) → [11,12) → [11.0,11.1) → [11.00,11.01)
```

[安装后](#快速开始)运行 `python scripts/run_examples.py` 可以重跑全部三个例子。[原始题目与结果](artifacts/readme-examples-20260923T090329Z/results.json)。这三个例子各测一次，用于直观展示接口；更多方法对照和失败情况见后文。

## 增加了什么能力？

| 能力 | Jev 原生接口 | 本项目 |
|---|---|---|
| 离散决策、选项概率 | 已支持 | 作为基本组件 |
| 按等级描述输出数值评分 | 已支持 | 并非本项目新增 |
| 通用数值读取，用户指定范围和精度 | 文档中没有专门的通用接口 | **多叉区间解码** |
| 数值网格上的分布 | 需定义候选值或额外映射 | **实验性阈值直方图** |
| 保证答案正确或概率校准 | 本实验未建立此保证 | **仍未建立** |

准确地说，Jev 本来就会返回数值评分和离散概率。本项目新增的是从这些决策到**数值域**的解码方式。参见官方 [Choice](https://docs.typesafe.ai/primitives/choice) 和 [Score](https://docs.typesafe.ai/primitives/score)。

## 方法：划分、选择、再细分

给定范围 `[L,U)`、分辨率 `ε` 和每层分支数 `K`：

1. 把当前区间分成最多 `K` 个互不重叠的子区间。
2. 用一次 Jev Choice 调用选择包含目标值的区间。
3. 沿该分支继续细分，直到只剩一个网格单元。
4. 返回最终区间，并用下端点作为数值读出。

真实值在上下文中给定为 `3230.78` 时，记录到的十叉路径为：

```text
[0,10000) → [3000,4000) → [3200,3300) → [3230,3240)
           → [3230,3231) → [3230.7,3230.8) → [3230.78,3230.79)
```

**六次离散选择，可以区分一百万个网格值。** 对 `N=(U−L)/ε` 个网格单元，最多需要 `ceil(log_K N)` 轮顺序决策。这个公式描述表示能力，不保证模型选对分支。

实现用整数网格索引和 Decimal 边界，支持非均匀大小的分支划分。默认每层十个选项。需要事先确定范围和精度；选错早期分支后，本实现不能回退。**最终小区间表示输出分辨率，并不是置信区间。**

## 实测结果

主体实验使用 OpenRouter 上的 `typesafe/jev-1.13-20260917`，没有微调，没有给模型检索工具。这是探索性的小规模实验；重复调用不等于新增独立样本。

### 股票指数历史回忆：平均相对误差 4.58%

问题明确为：标普 500 **价格指数在该年最后一个交易日的官方收盘点位**。只给日期和指数名，不给真实点位。统一从 `[0,10000)` 开始十叉细分，直到 `0.01` 点。两种选项顺序，各重复两次。

| 日期 | 真实点位 | 四次输出范围 | 绝对相对误差 |
|---|---:|---:|---:|
| 2019-12-31 | 3230.78 | 3331.10～3391.10 | 3.11%～4.96% |
| 2020-12-31 | 3756.07 | 3891.00～3999.99 | 3.59%～6.49% |
| 2023-12-29 | 4769.83 | 均为 4999.99 | 4.83% |

平均绝对相对误差（MAPE）为 **4.58%**，**11/12 次在 5% 以内**，最大误差 **6.49%**。所有输出都偏高。若改用“是否命中正确的 100 点区间”评价，直接选择和分层选择都是 0/12。

这是**历史事实回忆，不是行情预测**。真实值来自 [FRED](https://fred.stlouisfed.org/data/SP500)，并与同期新闻交叉核对，详见 [英文说明](README.md#historical-index-recall-458-mean-relative-error)及[完整记录](artifacts/jev-index-history-20260923T081058Z/report.md)。

### Ground-truth oracle input：读取误差 0%

保持题目措辞、模型、初始区间、分支数和顺序控制不变，只在输入中增加真实点位：

```json
"closing_level_index_points": "3230.78"
```

| 指标 | 不给点位 | 给定真实点位 |
|---|---:|---:|
| 直接选择正确的 100 点区间 | 0/12 | **12/12** |
| 分层定位到正确的 0.01 点区间 | 0/12 | **12/12** |
| 平均绝对相对误差 | 4.58% | **0%** |
| 所有逐层区间选择正确 | — | **72/72** |

这支持把“回忆数值”和“读取数值”分开研究。**Oracle input 指我们把答案直接放入上下文；它是读取对照，不是预测成绩。** 总共只有三个不同点位，不能推导出通用数值能力或任意精度保证。[原始对照记录](artifacts/jev-index-provided-20260923T081655Z/report.md)

### 其他方法表现如何？

12 道人工选择的算术题，含六道整数、六道可精确表示的小数；每道题两种顺序、两次重复，每种方法共 48 次评估。

| 方法 | 整数 /24 | 小数 /24 | 总正确 /48 | 顺序轮数 |
|---|---:|---:|---:|---:|
| 直接从 16 个数值中选择 | 24 | 16 | **40** | 1 |
| **四叉区间解码** | **24** | **15** | **39** | **2** |
| 显式候选集合归属 | 24 | 14 | 38 | 1 |
| 十进制逐位，提供已选前缀 | 24 | 8 | 32 | 2 / 4 |
| 自适应阈值搜索 | 24 | 4 | 28 | 4 |
| 并行阈值＋单调修正 | 24 | 4 | 28 | 1 |
| 独立二进制位，明确提示 | 16 | 12 | 28 | 1 |

**小候选集上，直接选数值仍略好。** 分层法的吸引力在于不用一次列出所有精细候选值，而非本实验已经证明它最准确。不同方法的独立问题合并调用，表中的轮数是依赖深度，不是独立测量的延迟。

失败现象包括：

- **编码转换增加了任务负担。** 问“属于哪组明确列出的值”得到 38/48；问相应二进制位只得到 28/48。
- **提示词会改变结果。** 较早的位预测对照中，明确位权和计算公式后，从 6～7/24 提升到 14～15/24。
- **小数任务更难。** 阈值比较和十进制逐位在这批小数题上失误明显更多。
- **阈值概率不一定单调。** 25/48 次出现矛盾，例如 `P(Y≤0.4375)=0.57`，却有 `P(Y≤0.5)=0.01`。

这些结果不能证明其他方法永远不可行。[全部方法结果](artifacts/jev-alternatives-20260923T080125Z/report.md) · [提示词和顺序对照](artifacts/jev-binary-controls-20260923T075624Z/report.md)

补充测试也体现了敏感性：使用**两个分支和不同提示词**的通用解码器时，六次闭卷回忆的 MAPE 为 **31.17%**，六次给定真实值的读取仍全对。它不是仅改变分支数的严格消融，不能把差异归因于分支数；但它说明 **4.58% 必须限定到原来的十叉协议**。[补充结果](artifacts/binary-api-20260923T085013Z/summary.json)

## 能输出分布吗？

贪心走一条路径只能得到点读出，不能提供整个数值分布。`estimate_distribution` 另外实现了阈值提问 → 单调回归修正 → 区间概率质量的实验性接口，同时保留原始 CDF 和单调性违规数。

该直方图假设支持范围为 `(lower,upper]`，使用右闭区间。中点加权可以近似计算期望。**让概率形状合法，不代表概率准确或已经校准。** 前面的不单调结果正是需要保留的限制。用法见 [英文说明](README.md#what-about-distributions)。

## 快速开始

```bash
git clone https://github.com/Bring-AI/jev-numeric.git
cd jev-numeric
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# 在 .env 填入自己的 API 凭据。
```

```python
from jev_numeric import JevClient, decode_number

with JevClient() as client:
    result = decode_number(
        client,
        state={"closing_level_index_points": "3230.78"},
        target="the supplied closing level in index points",
        lower="0", upper="10000", resolution="0.01", branching=10,
    )
print(result["value"])
print(result["trace"])
```

复现首页结果请用保留原始提示词的实验脚本；通用 API 使用通用提示词，不与原协议混为一谈。

```bash
# 无需 API 的离线检查
pytest -q
python scripts/verify_artifacts.py
python scripts/build_artifact_summary.py

# 真实 API 调用，需要凭据，会产生费用
python scripts/probe_jev_index_history.py
python scripts/probe_jev_index_history.py --provided-close
python scripts/probe_jev_alternatives.py
python scripts/probe_jev_binary_controls.py
```

[artifacts](artifacts/) 保留原始请求、选项排列、返回概率及模型标识；不含鉴权头。新实验写入被忽略的 `runs/`。[指标](artifacts/metrics.json)由已保存结果重新计算，[哈希清单](artifacts/manifest.json)用于核对文件完整性。

本项目是基于决策接口的数值输出探索，不是训练出的新回归模型，也尚未验证 OOD 或概率校准。代码和原创文档/图片采用 [MIT](LICENSE)。非 TypeSafe 官方项目。
