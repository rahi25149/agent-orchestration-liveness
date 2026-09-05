# Agent Orchestration Liveness 中文说明

这个 Skill 用于协调长期运行的架构师、工程执行者与独立只读监督者工作流，同时明确区分所有权、存活状态、完成层、用户汇报和独立监督。

两份 README 都只是简介，不构成第二权威。执行时遵循 `SKILL.md`、实际触发的 references，以及当前用户／项目声明的工作模式；文件语言不决定指令优先级。

## 正常运行路径

- **结果批次：** 只有服务于同一个外部可验证结果，并共享同一套通过／失败验收边界的工作，才归入同一批次。
- **按模式监督：** 项目选择 timer-only 时排他生效，通用事件／检查点不追加审查。GREEN 留在监督自己任务的规定快照，对外静默。
- **风险触发技术复查：** 只有受保护语义发生变化，且晚发现代价与独立发现价值足以覆盖复查成本时，才启用独立复查；低风险可逆修改继续走自检快车道。
- **受限复查成本：** 每次只复查一个不变量或直接生产者—消费者路径，复用有效的 Worker 证据，至少做一次面向证伪的独立检查，并允许无依赖工作继续推进。
- **有界连续工程：** 在同一假设、授权与 repair budget 内连续调查、实现、必要验证；真实外部副作用首败停止，UNKNOWN 绝不重发。
- **有界架构师执行：** 只允许架构师直接处理一个已声明的阻塞假设或原子集成动作，并要求停止条件和交接目标。
- **真实完成层：** 在首次可执行的最小切片上观察真实浏览器、桌面、设备或远程会话后，才声明对应的更高完成层。
- **监督状态分离：** 分开维护编排存活状态、监督发现状态、架构师处置结论以及阻塞／确认元数据。
- **低噪音通信审计：** 每个区间保留一条可检查的内部通信审计记录，但不把健康状态机械播报给用户。
- **长寿命上下文默认：** native compaction 加有界当前状态；context 大小、经过时间与压缩本身均不授权轮换。必要 Goal 交接仍需受支持的 paused 预置、冻结／读回、单一权威与已核验回退。
- **休眠研究退出热路径：** metrics、cohort／权限探针、writer 与 hook 研究只有在另获明确授权、非关键且有业务成本上限时读取和运行，普通派工／状态更新不加载。

## 文件说明

- `SKILL.md`：角色、生命周期、完成层、汇报和监督的核心规则。
- `references/outcome-batching-and-review-budget.md`：结果批次、实质变化、检查点、架构师有界执行、技术审查交接和监督发现收口。
- `references/technical-review-workflow.md`：两阶段触发门、受限交接、证伪检查、`TECH_CLEAR`／`TECH_BLOCKED`、增量复查、新鲜度和流程税护栏。
- `references/interactive-runtime-lifecycle.md`：真实界面最小探针、唯一运行 owner、任务级保活、授权判断、`USER_WAIT` 与安全清理。
- `references/user-reporting-boundaries.md`：内部事件与用户可见汇报边界，以及通信审计证据。
- `references/review-exchange-templates.md`：架构师与监督者之间的审查、处置和发现状态模板。
- [Context Lifecycle](references/context-lifecycle-and-runtime-metrics.md)：正常有界角色状态、native compaction、权限／owner 连续性、Goal-aware 安全交接与回退；旧路径保留兼容。
- [Dormant Context Experiments](references/context-experiments.md)：另行授权的 measured-role 探针、安全 JSONL 指标、研究阈值、hook 和 App Server writer 生命周期。
- `scripts/context_metrics.py`：只依赖 Python 标准库的严格 JSONL 追加、校验与 baseline／pilot 对比脚本。
- `scripts/test_context_metrics.py`：schema 安全与决策阈值的确定性测试。
- `scripts/app_server_usage_adapter.py`：严格合并 App Server 通知；每个已完成 turn 只持久化一条不含正文的用量记录。
- `scripts/test_app_server_usage_adapter.py`：覆盖隐私、重放、乱序和失败闭合的确定性测试，以及需显式开启的真实 App Server 烟测。
- `scripts/desktop_rollout_usage_adapter.py`：为无法直接旁路其独立 stdio App Server 连接的 Codex Desktop fresh thread 提供显式预武装桥接。
- `scripts/test_desktop_rollout_usage_adapter.py`：覆盖预武装、精确路由、重放、压缩代次、隐私和终态边界的确定性测试。

## 研究可选，不是开工前置

研究脚本及其确定性验收矩阵保持不变。仅在显式授权和成本边界内，或为关闭既有 measured operation 所必需的恢复，读取 [Dormant Context Experiments](references/context-experiments.md)。Recorder 测试通过不授权真实 App Server turn、采样、hook、轮换或配置变更；不要从 README 自动进入 Phase 1 或恢复历史 cohort。

普通工作只在首次进入相关模式、reference 内容变更或当前已缺失必要内容时完整读取；已读且仍完整、有效的内容可复用，不每次派工或 state delta 重读。真正必要的当前事实和安全检查不因此省略。

具体模型／推理路由、业务门、机器、凭据、端口和 cadence 仍由项目指令或有界当前状态声明。
