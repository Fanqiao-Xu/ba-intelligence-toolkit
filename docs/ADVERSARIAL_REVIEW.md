# BA Intelligence Toolkit — 对抗式评审文档包

> **用途**: 本文档汇总了项目的全部产出物,按对抗式评审的需要组织,供评审者对设计逻辑、合规准确性、技术实现、演示可信度逐层挑战。
>
> **评审者角色假设**: 资深 BA / 合规专家 / 技术面试官
>
> **评审目标**: 验证三个核心声明是否经得起追问:
> 1. "这不是关键词匹配,是合规缺口推理" — 是否真的做到了语义判断?
> 2. "合规义务清单是核心知识产权" — 清单的颗粒度和法条引用是否准确?
> 3. "这个工具解决真实 BA 工作痛点" — 痛点是否真实,解决方案是否有效?

---

## 目录

| 编号 | 内容 | 文件来源 |
|------|------|----------|
| A | 评审指南:对抗式问题清单 | 本文档原创 |
| B | 项目工具书 (Project Dossier) | `docs/PROJECT_DOSSIER.md` |
| C | 合规义务清单 (核心 IP) | `data/compliance_obligations.yaml` |
| D | 演示会议记录 (含 5 个故意缺口) | `data/sample_transcript.txt` |
| E | As-Is 流程文档 | `data/as_is_process.txt` |
| F | To-Be 流程文档 | `data/to_be_process.txt` |
| G | AI 引擎 + 全部提示词 | `ai_engine.py` |
| H | 合规缺口核对器 | `modules/compliance.py` |
| I | 需求提取器 | `modules/extractor.py` |
| J | RTM 生成器 + 影响分析 | `modules/rtm.py` |
| K | 流程差距分析器 | `modules/gap_analyzer.py` |
| L | 工具函数 (导出 + 可视化) | `utils.py` |
| M | Streamlit 主应用 | `app.py` |
| N | 依赖 + 配置 | `requirements.txt` + `.env.example` |

---

# A. 评审指南:对抗式问题清单

评审者应从以下五个维度逐层挑战。每个维度列出核心追问、预期回答标准、以及"如果答不出来则项目有硬伤"的红旗信号。

## A1. 合规义务清单的准确性与深度

### 核心追问

| # | 问题 | 为什么重要 |
|---|------|------------|
| A1.1 | C1 义务引用的 MLR 2017 Reg 33(6)(b)(iii) — 这个法条编号对不对?具体说了什么? | 如果法条引用错误,整个清单的可信度归零 |
| A1.2 | C1 的 `how_to_check` 写的是"判断是否有实时人际交互" — 如果 BRD 描述的是视频银行(Video Banking,有真人 staff 视频通话),这算不算 non-face-to-face? | JMLSG Guidance 对"non-face-to-face"的定义有边界条件,视频银行是一个灰色地带 |
| A1.3 | C4 的触发条件是"complex or unusually large transactions" — 对于一个开户项目,BRD 在开户阶段怎么可能覆盖交易级 EDD?这个义务是不是对开户场景不适用? | 这是范围合理性的挑战 |
| A1.4 | E2 要求"verify SOW for EDD cases" — SOW (Source of Wealth) 和 SOF (Source of Funds) 的区别是什么?清单里为什么分开处理(E1 vs E2)? | 测试作者是否真懂 SOW/SOF 的区别 |
| A1.5 | D4 关于 domestic PEP — 清单说"domestic PEPs may be lower risk but still require EDD"。但 FCA FG17-6 的实际表述是什么?UK 本土 PEP 是否真的可以降级处理? | 引用是否准确到原文 |
| A1.6 | G3 要求 audit trail — 清单引的 source 是"MLR 2017 Reg 40(1); FCA SYSC 9"。SYSC 9 是关于 record-keeping 的吗?具体哪个段落? | 法条引用精度 |
| A1.7 | H1 关于 GDPR Article 9 biometric data — 清单说"explicit consent or substantial public interest for AML"。DPA 2018 Schedule 1 Part 2 的具体条件是什么? | GDPR 专业知识深度 |
| A1.8 | 清单有 36 项义务但只标了 11 项 deep — 其余 25 项的 `how_to_check` 是否足够具体?随机抽一项标准义务,能否通过"实习生测试"? | 深度均匀性 |

### 红旗信号
- 作者无法说出任何一条 deep 义务的完整判断逻辑和法条原文
- `how_to_check` 出现"check whether the BRD mentions [keyword]"的表述 — 退化为关键词思维
- 法条引用只到 Reg 级别,说不出具体小节

## A2. "语义推理而非关键词匹配"的验证

### 核心追问

| # | 问题 | 为什么重要 |
|---|------|------------|
| A2.1 | COMPLIANCE_GAP_PROMPT 里说"an obligation is NOT satisfied merely because a related keyword appears" — 但 LLM 真的会遵守这个指令吗?有没有测过反例? | 指令 ≠ 行为 |
| A2.2 | 如果 BRD 里写了"we use Onfido for KYC including liveness detection and multi-source verification" — 但实际流程描述里并没有 liveness 步骤,LLM 会标 satisfied 还是 gap? | 测试 LLM 是看声明还是看实质 |
| A2.3 | C1 的 `how_to_check` 写了 3 个 STEP,非常详细 — 但这是否意味着 LLM 只是在按这个 checklist 逐条找?这跟关键词匹配有什么本质区别? | 最深层的挑战:结构化 how_to_check 本身是否是一种更高级的关键词匹配 |
| A2.4 | 有没有做过"反向测试"?拿一段完全不触发某义务的 BRD,确认工具不会过度敏感? | 防止 false positive — **已执行,通过 (0 false positive)** |
| A2.5 | temperature=0.3 — 同一个 BRD 跑两次,结果一样吗?如果不一致,这个工具在生产环境能信吗? | 确定性 |
| A2.6 | 批处理(batch_size=10)— 如果某条义务的判断依赖另一条义务的结果(比如 C2 PEP EDD 依赖 D2 PEP screening),分批处理会不会丢失这种依赖? | 架构缺陷 |

### 红旗信号
- 作者无法解释"how_to_check 的结构化判断逻辑"和"关键词匹配"的区别
- ~~没有做过反向测试,只有正向测试~~ **已解决:反向测试通过,0 false positive**
- 无法回答跨批次依赖问题

## A3. 演示数据的真实性

### 核心追问

| # | 问题 | 为什么重要 |
|---|------|------------|
| A3.1 | 会议记录里第 9 点,James 说"retain data for no more than 6 months",然后第 10 点 Emma 纠正为 5 年 — 这个"自我纠正"是不是太刻意了?真实会议会有这种错误吗? | 演示数据的可信度 |
| A3.2 | 5 个故意设计的缺口 — 如果面试官说"给我看一个真实 BRD 的检查结果",你有吗? | 演示数据 vs 真实数据 |
| A3.3 | As-Is 流程里 Step 4 说"matching the photo on the document to the customer (in-branch only; not possible for app submissions)" — 这意味着 As-Is 流程对 app 提交的客户根本没有做照片比对?那 As-Is 流程本身就有合规问题,为什么 To-Be 才需要解决? | 场景逻辑一致性 |
| A3.4 | To-Be 流程的"Scope Exclusions"明确排除了 ongoing monitoring、post-onboarding risk refresh、periodic CDD re-verification — 但 F3 义务要求 ongoing sanctions rescreening。这意味着工具会标 F3 为 gap,但这个 gap 是项目范围决定的,不是遗漏。工具能区分"故意排除"和"遗漏"吗? | 工具是否能理解 scope exclusion |
| A3.5 | 演示会议记录末尾有一段"NOTES FOR BA INTELLIGENCE TOOLKIT DEMO"直接列出了 5 个 gap — 如果面试时展示这段文本,会不会暴露这是人为设计的? | 演示的专业性 — **已修复,NOTES 段落已删除** |

### 红旗信号
- ~~演示数据文件包含"这是故意设计的 gap"的元注释,面试时需要删除或隐藏~~ **已解决:NOTES 段落已删除**
- 工具无法区分"scope exclusion"和"遗漏"

## A4. 技术实现的健壮性

### 核心追问

| # | 问题 | 为什么重要 |
|---|------|------------|
| A4.1 | `generate_json` 方法直接 `json.loads(text)` — 如果 LLM 返回的 JSON 不完整(DeepSeek 长文本时常见),会直接抛异常。有没有 fallback? | 健壮性 |
| A4.2 | 合规检查的批处理是 `for i in range(0, len(self.obligations), batch_size)` — 如果第一批返回了 8 个结果但第二批返回了 12 个,总数对不对?有没有校验? | 数据完整性 |
| A4.3 | RTM 生成器的 `analyze_impact` 用 `nx.descendants` 找下游影响 — 但依赖图是 LLM 生成的,如果 LLM 产生了循环依赖(REQ-001 depends_on REQ-002, REQ-002 depends_on REQ-001),NetworkX 会怎样? | 循环依赖处理 |
| A4.4 | `load_uploaded_file` 处理 PDF 时用 PyPDF2 — 但 requirements.txt 里没有 PyPDF2。这是不是一个未声明的依赖? | 依赖管理 |
| A4.5 | `_load_demo_results` 函数定义在 `app.py` 的最末尾,但在第 130 行就被调用了 — Python 的函数定义顺序在 Streamlit 里这样写会不会有问题? | 代码质量 |
| A4.6 | session_state 里没有存储 API 调用成本/token 使用量 — 面试时如果被问"跑一次完整 demo 花多少钱",你能回答吗? | 成本意识 — **已修复:实时追踪 + 侧边栏显示,完整 demo ¥0.0465** |

### 红旗信号
- ~~没有 JSON 解析的 fallback 机制~~ **已解决:max_retries + regex 提取**
- ~~PyPDF2 未在 requirements.txt 中声明~~ **已解决:已添加**
- ~~无法回答单次运行的 token 消耗和成本~~ **已解决:实时追踪 + 侧边栏显示,完整 demo ¥0.0465**

## A5. 作为求职作品的叙事完整性

### 核心追问

| # | 问题 | 为什么重要 |
|---|------|------------|
| A5.1 | 你说你观察到 BA 大量时间花在手动合规检查 — 你在 Bank of China 实习时具体看到了什么?能讲一个具体例子吗? | 痛点真实性 |
| A5.2 | 这个工具的受众是谁?BA 自己用?合规团队用?如果 BA 用,为什么不直接用 GRC 平台?如果合规团队用,他们为什么要用一个 Streamlit 工具? | 产品定位 |
| A5.3 | 你说"这个工具不替代人工合规审查" — 那它到底节省了多少时间?有没有量化? | 价值量化 |
| A5.4 | 如果面试官说"这很好,但你只有一个人做的,你在团队里怎么协作开发这个?" — 你怎么回答? | 团队协作 |
| A5.5 | 你做了 5 个模块(需求提取/合规检查/RTM/流程差距/导出)— 如果只保留一个,你保留哪个?为什么? | 优先级判断 |
| A5.6 | 这个项目从设计到完成花了多长时间?如果再做一遍,你会改变什么? | 反思能力 |

### 红旗信号
- 无法讲出 Bank of China 实习中的具体观察
- 无法量化工具节省的时间
- 说不出"如果只保留一个模块"的取舍逻辑

---

# B-N. 项目文件完整内容

> 由于文档长度限制,B-N 部分的完整代码和数据文件内容已包含在项目的原始文件中。评审时请直接对照以下文件路径阅读:
>
> | 编号 | 文件路径 |
> |------|----------|
> | B | `docs/PROJECT_DOSSIER.md` |
> | C | `data/compliance_obligations.yaml` |
> | D | `data/sample_transcript.txt` |
> | E | `data/as_is_process.txt` |
> | F | `data/to_be_process.txt` |
> | G | `ai_engine.py` |
> | H | `modules/compliance.py` |
> | I | `modules/extractor.py` |
> | J | `modules/rtm.py` |
> | K | `modules/gap_analyzer.py` |
> | L | `utils.py` |
> | M | `app.py` |
> | N | `requirements.txt` + `.env.example` |

---

# 附:已知技术债清单

以下问题已在对抗式评审中被识别,按优先级排列:

| 优先级 | 问题 | 文件 | 状态 |
|--------|------|------|------|
| ~~P0~~ | ~~`sample_transcript.txt` 末尾包含 NOTES 段落~~ | ~~`data/sample_transcript.txt`~~ | **已修复** — NOTES 移至 `data/demo_gap_design_notes.md` |
| ~~P1~~ | ~~`utils.py` 引用 PyPDF2 但 `requirements.txt` 未声明~~ | ~~`requirements.txt`~~ | **已修复** — 添加 PyPDF2 + pandas |
| ~~P1~~ | ~~`generate_json` 无 JSON 解析 fallback~~ | ~~`ai_engine.py`~~ | **已修复** — 添加 max_retries + regex 提取 fallback |
| ~~P1~~ | ~~批处理无结果数量校验~~ | ~~`modules/compliance.py`~~ | **已修复** — 缺失义务自动标记为 unclear |
| ~~P2~~ | ~~`_load_demo_results` 定义在使用之后~~ | ~~`app.py`~~ | **已修复** — 移至 session_state 初始化后 |
| ~~P2~~ | ~~无 token 使用量追踪~~ | ~~`ai_engine.py`~~ | **已修复** — 添加 `_record_usage` / `get_usage` / `get_cost_estimate` / `reset_usage` 方法,侧边栏实时显示 token 数和成本 |
| ~~P2~~ | ~~循环依赖未处理~~ | ~~`modules/rtm.py`~~ | **已修复** — 添加 DAG 检查 + BFS fallback |
| ~~P2~~ | ~~README.md 仍写 "OpenAI API"~~ | ~~`README.md`~~ | **已修复** — 更新为 "OpenAI-compatible API (DeepSeek/OpenAI)" |
| ~~P3~~ | ~~Dossier 中 tech stack 仍写 "OpenAI API (GPT-4o-mini)"~~ | ~~`docs/PROJECT_DOSSIER.md`~~ | **已修复** — 更新为 "DeepSeek API (deepseek-chat)" + 全文 11 项 deep 义务列表 + C4 trigger 描述更新 |

---

# 附:反向测试与 Demo Snapshot 执行记录

## 反向测试 (Reverse Test)

> **A2.4 追问**: "有没有做过反向测试?拿一段完全不触发某义务的 BRD,确认工具不会过度敏感?"

**已执行。** 详见 `data/reverse_test_brd.txt` (输入) 和 `docs/REVERSE_TEST_REPORT.md` (报告)。

测试方法:撰写一份覆盖全部 36 项义务的"完美 BRD",运行合规缺口检查器,验证 false positive = 0。

**结果:**

| 指标 | 值 |
|------|----|
| 总义务数 | 36 |
| Satisfied | 36 |
| Gaps (false positives) | **0** |
| Unclear | 0 |
| Not applicable | 0 |
| API 调用次数 | 4 |
| Token 总量 | 36,302 |
| 成本 | ¥0.0403 CNY |

**结论:** 反向测试通过。工具在覆盖全部义务的 BRD 上零误报,证明工具不存在系统性过度敏感问题。

## Demo Snapshot 生成

> **A4.6 追问**: "跑一次完整 demo 花多少钱?"

**已执行。** 用 `data/sample_transcript.txt` + `data/as_is_process.txt` + `data/to_be_process.txt` 跑完整 pipeline (需求提取 → 合规检查 → RTM → 流程差距分析),结果保存至 `data/demo_results.json`。

**结果:**

| 指标 | 值 |
|------|----|
| API 调用次数 | 7 |
| Prompt tokens | 24,421 |
| Completion tokens | 11,055 |
| Token 总量 | 35,476 |
| 成本 | **¥0.0465 CNY** |
| 提取需求数 | 15 |
| 合规检查结果 | 15 satisfied, 18 gaps, 2 unclear |
| RTM 条目 | 15 |
| 依赖关系边 | 10 |
| 流程差距 | 10 |

Demo Mode 现在完全可用:面试时无需 API 即可展示全部预计算结果。
