---
name: agent-orchestration-liveness
description: Coordinate long-running or multi-agent work requiring Architect/Worker/Supervisor separation, bounded ownership, liveness, low-noise reporting, truthful completion, safe handoffs, agent-context lifecycle management or measurement, or orchestration of long-lived browser, desktop, device, or remote sessions. Do not use for short single-owner work, routine code review, standalone product planning, or one-off machine operation without orchestration needs.
---

# Agent Orchestration Liveness

## 保持角色与权威分离

- **Architect** 是唯一业务权威：拥有目标、业务门、优先级、owner、派工、验证与复审预算、产品与架构裁决、集成和验收。Architect 只可为一个已声明的阻塞假设或原子集成动作临时直接执行；出现 first stable failure、范围扩张或 Worker 可接手时立即退出。
- **Worker** 只拥有一个 bounded assignment 与其 write hotspot；在授权范围内自主执行，遇到 first stable failure 即停止并返回当前事实，不扩大范围，不夸大完成层。
- **Supervisor** 是独立只读审计角色：检查 goal alignment、liveness、ownership、冲突、truthful completion 与浪费；不派工、不审批、不实现、不操作机器，也不成为第二 Architect 或常驻 technical reviewer。
- **Controller** 若存在，只管理有界状态、liveness、transport 或内容无关指标；不选择业务任务、owner 或验证预算，不创作或修补业务 packet，不代收审批，不冒充用户。机械 transport 只能逐字传递 Architect 已完成的内容。

把普通代码复核、测试复核和缺陷裁决放入独立的 risk-triggered technical-review workflow。需要 independent review 时，reviewer 不得是 primary implementer；Technical reviewer 与 Supervisor 权限分离。低风险、可逆、局部可测的变更不建立常驻 reviewer、heartbeat、Worktree 或 approval gate。

编排复杂度必须匹配已证的协调或连续性风险。单 Agent、单 owner 且可有界闭合、无此类风险的任务，不因本 Skill 新增 Supervisor、Controller、heartbeat、handoff/rotation 或 context protocol；独立安全规则仍照常适用。

## 维护最小当前事实

维护一张有界 state card，至少记录：当前 objective/gate 与 acceptance boundary、outcome batch、active owner 与 hotspot、独占 operator、每项 assignment 的 next observable checkpoint、真实外部 wait、最高已证 completion layer、OPEN findings、最近 material delta、下一安全动作，以及是否真的需要用户。

State card 只是索引，不是不可质疑的事实源。作出 material direction、completion、conflict、risk 或 handoff 判断前，只抽样一个最小直接当前事实；不要重扫仓库、重跑已通过测试或重建证明链。旧 revision、PID、订单、线程状态与错误码默认都是历史，除非当前工作重新使其相关。

用稳定的完整 role/thread identity 路由；标题和 transport metadata 不能代替身份。把 delivery failure 与业务任务状态分开报告。

## 组织 bounded work 与安全并发

每个 Worker assignment 至少包含：assignment 与 gate、当前已证事实或首个未知、一个可外部核验 outcome、owner/hotspot、明确 exclusions、最小充分 acceptance、first-stable-failure 停止条件、semantic verification budget、next checkpoint 和 completion packet 要求。

一个 outcome batch 只对应一个 externally verifiable outcome 与一个共享 pass/fail boundary。普通返修、technical review 和内部 owner handoff 留在同一 batch，除非外部 outcome 或 acceptance boundary 发生 material delta。

Architect 在新 gate、batch 开闭、Worker completion handshake 和独占资源 wait 后重扫 ready lanes：

- 对当前目标相关、已授权、可独立闭合、热点与独占资源不冲突、不会互相使证据失效的 lane，默认并发派到项目安全上限。
- 并发数是上限，不是配额；不得为凑数拆碎原子 outcome、创建无关 Worktree、Reviewer、Supervisor 或调查。
- 少于两个合格 lane 时，记录一个具体的依赖、共享契约、hotspot、独占资源、权威事实或故障扩散原因；单写 SERIAL 或 NONE 不充分。
- 保持 one writer per hotspot 与 one executable owner per exclusive resource。一个局部 blocker 只冻结依赖它的动作，其他安全且相关工作继续。

已 PASS 的 evidence 在同一精确 candidate 与覆盖范围未变化时复用。只有 covered candidate 变化、修复失败项、相关环境或证据失效，或晋级更高 completion layer 需要 representative real-surface evidence 时才重跑。减少重复不等于跳过资金、身份、授权、幂等、生产、安全或首次完成声明所需的验证。

## 判断 liveness 并闭合结果

每个受监督对象只取一个 liveness 状态：

- **ACTIVE_WORK**：具名 owner 正在推进当前 gate 或其声明依赖，并有 next observable checkpoint。
- **BOUNDED_WAIT**：具名的非用户操作、观察或依赖仍在声明边界内。
- **USER_WAIT**：确实需要身份澄清、登录或验证码、桌面解锁、UAC、物理输入、新凭据或权限、真实资金或生产授权。
- **STALLED**：gate 未完成，存在安全且相关的下一动作，却没有 owner 执行或确认。
- **COMPLETED**：声明的 gate 与全部 required handoff 均已闭合。

Activity 不等于进展。编译修复、必要测试、migration、依赖恢复和集成可保持 ACTIVE_WORK，但必须说明正在减少的依赖或未知与下一边界。授权内、可逆、本地的 owned action 不是 USER_WAIT；evidence required 不等于 approval required。

不得因与当前 ready bounded action 无关的 governance 延迟执行。只有在当前触发点由本 Skill、项目契约或独立安全规则明确要求，且直接保护该动作的 Goal/stop/budget、ownership/authority、authorization/approval、safety、handoff、completion truth 或 irreversible effects 的检查与 reference，才是 fail-closed 前置条件。此类必要事实缺失、过期、歧义或 lifecycle 不受支持时不得推进。例行或 advisory Supervisor review 不是 approval gate，除非明确要求暂停受影响动作。

Worker 完成时返回一个压缩 packet：assignment/outcome batch、当前 gate 与 acceptance boundary、结果与状态变化、最高已证层、first stable failure、owned runtime/config/resource/pending 的安全状态、唯一允许下一动作、是否需要用户及稳定原因、technical-review disposition。Architect 必须确认后只做三选一：关闭 assignment/gate、派发下一 bounded action 与 owner，或声明真实的 bounded/user wait。工具结束本身不构成闭环；BLOCKED 只是输出协议，实际 liveness 仍按缺失事实的 owner 与性质分类。

Completion packet 已可读但 delivery 状态不明时，视为结果已经收到，只标记缺失的 Architect ACK；不得重跑测试、订单或机器动作来验证 transport。

发现漏接 completion 或 Architect 在安全下一动作存在时 idle，只唤醒一次并指出缺失决定；不代替派工，不快速轮询，不在一个 heartbeat interval 内重复同一纠偏。

## 如实声明完成层并压缩用户汇报

只声明最高已证层：

- **engineering complete**：bounded implementation/repair 与直接检查通过；
- **integration complete**：受影响组件通过声明的集成路径；
- **user-capability complete**：目标用户可见或真实环境 outcome 在 acceptance conditions 下被观察。

低层证据不得暗示高层完成。Mock、simulator、unit test、process start 或 API response 不能自动证明真实设备、真实资金、真实用户流或完整业务结果。**TECH_CLEAR** 只覆盖声明的 scope、candidate 与 layer；依赖 browser、desktop、device 或 remote session 的高层声明，必须先有 representative real-surface evidence。

Architect 是用户沟通的压缩层。Worker 生命周期、普通测试、返修、review、ACK、commit 与 re-dispatch 默认留在内部。仅在 objective/gate、material risk、真实 USER_WAIT/RED、用户声明的报告边界，或已证明的 user-visible completion 发生变化时更新用户；GREEN heartbeat 静默。同一事实不重复播报。

降噪不能压掉内部 truth：blocker、data anomaly、safety risk 和 inability to continue 必须立即到 Architect；一旦形成真实用户门、RED、material expectation change 或 decision need，再由 Architect 及时报告用户。

## 运行独立监督

Heartbeat 与 liveness-only review 只在用户、项目或当前目标声明的 cadence/checkpoint、completion-ACK deadline 或 retry-cap boundary 运行；未声明 recurring cadence 时，以当前 active assignment 的 next observable checkpoint 作为一次性 review boundary，不建立通用时间间隔。它保持原 batch，不自动成为 material event review 或新 finding。需要判断 OPEN finding 状态的 follow-up 属于一次 material review；若同时命中 liveness boundary，合并到该次 review，绝不另跑一次 liveness-only review。工具调用、commentary、同因支撑重试或状态轮询只有在产生 gate-relevant 新事实、减少声明的依赖或未知时，才重置 last-material-progress boundary。相关工作健康时保持静默。

只有存在明确的跨 review-boundary 监督义务时，才维护一个 gate-scoped、read-only Supervisor，例如 OPEN finding、已声明的 recurring heartbeat/checkpoint、completion ACK 后续检查或 finding follow-up。预计耗时长、GUI/remote 或独占资源本身只提高风险，不单独触发持续 Supervisor。同一 gate 最多一个；其 epoch 只覆盖一个 gate、outcome batch 或 related finding cluster，并只持有不超过 2 KiB 的 Supervisor overlay：reviewed Architect revision、稳定 finding IDs/states、last gate-relevant progress、last review boundary 与 next supervision boundary。每次复核仍抽样最小当前事实，不复制完整 gate、业务计划、日志或 transcript。

当 externally verifiable outcome、acceptance boundary、authority/risk boundary 或 claimed completion layer 发生 material change，出现 exclusive-resource conflict，或 OPEN finding 到达 next-check boundary 时，执行 material event review；已有 gate-scoped Supervisor 时复用它，不创建第二个，也不在 finding 与其紧邻复审之间轮换。没有跨边界持续义务的离散 event review 才使用 fresh、read-only、short-lived Supervisor，结果返回后结束线程。Gate close、暂停、真实 USER_WAIT、确无安全下一动作或监督价值结束时，先 reconcile findings，再结束 gate-scoped Supervisor。只有用户或当前业务权威明确决定迁移，或直接证据表明 Supervisor 的 role、project、revision、finding 或 communication continuity 已不可信且一次有界原地修复失败时，才在安全边界用 bounded overlay 做 Supervisor-to-Supervisor handoff。普通 commit、test、same-batch repair、TECH result、owner handoff 或 integration preparation 不自动触发新 Supervisor。

每个 actionable finding 使用稳定 ID，并保持 OPEN，直到一个当前事实把它变为 CLOSED 或 SUPERSEDED；复发创建新 finding。Architect disposition 只能是 ACCEPTED、PARTIALLY_ACCEPTED 或 REJECTED_WITH_EVIDENCE，它不是 finding state。Gate 关闭时不得让 OPEN finding 静默消失。

Supervisor 只提供 advisory：

- **GREEN**：目标一致、owner 清楚、声明真实或等待合理；保持静默。
- **YELLOW**：首次漏接、方向偏差、无理由停滞、ownership/truthfulness 或 communication concern；通知 Architect 并设 response boundary，不自动暂停工程。
- **RED**：同一 YELLOW 跨两个 review boundary 未解决、独占资源发生双控制，或新动作威胁生产、凭据、资金、数据完整性或不可恢复状态；只暂停受影响动作，其他安全工作继续。

维护一张 compact supervision card：gate/acceptance、liveness、highest layer、last material progress、owners/hotspots/operator、wait/deadline、最小 evidence、communication audit、OPEN findings、至多一个最高杠杆纠偏、next safe action、user-required fact 和 severity。问题解除后立即清除旧 warning。

## 安全管理 context 与按需 handoff

Native compaction 只是 context safety valve，不是 workflow authority。保持一份有界 Architect authority snapshot 与更小的 Supervisor overlay；复用有效工程 ownership，不复用 unbounded chat history。

项目原生、长寿命 Architect 配合 native compaction 与 bounded state 是默认模式。Elapsed time、turn count、context 占比、high-context、目标变化或一次及多次成功 compaction 只能触发 freshness、质量、延迟与成本复核，均不得单独触发 handoff。只有用户或当前业务权威明确决定生命周期迁移，或直接证据表明 authority、Goal、project、route、capability、transport 或 working-mode continuity 已不可信且无法原地有界修复时，才启动 fresh handoff。Fresh start 前即时复核 queued/resumed work、现有 completion、owner、reviewer 与独占动作。使用 fresh thread + bounded bootstrap；禁止 full-history fork 伪装重置。

Successor 先核验最小当前事实。其 continuity check 完成且无必要事实或外部 wait 后的第一个响应就是 **first actionable turn**，必须同时执行首个正确推进动作；需要派工时给完整 DISPATCH_PACKET，缺必要事实时返回一个精确 BLOCKED。消费既有 completion 后、首次 dispatch 前重新扫描 ready lanes，不继承 incumbent 的旧 SERIAL 判断。

Persisted Goal 若存在，是独立的 thread-scoped continuation contract，不会从 project、prompt、authority snapshot 或 bootstrap 自动继承。Goal 的 exact objective、stop/completion conditions 与 budget scope 只由用户或 Architect 定义；Controller 不概括或创作。任何 Goal-aware handoff 都必须用受支持的 set/read lifecycle，在 authority 切换时保持单一权威、禁止双 active，并在状态不明时 fail closed、保留 incumbent。Goal continuity 不替代 direct role channels、Worker completion handshake、existing-owner reconciliation、first advancing action 或 first clean outcome。

保持 incumbent 的实际 route 与 effective least-privilege capability。Filesystem capability 不扩大业务 authorization。Controller 永远不是 approval reviewer，不点击、relay、转换或代用户批准；授权账本内普通动作应由 owning role 自主闭环。Fresh capability/profile mismatch 是 controller/setup defect，不是 USER_WAIT；approval 留下 untouched，并在安全边界纠正。只有真实红门才找用户。

Continuity ACK 只建立 PROVISIONAL transfer。Prior role 保持 read-only、recoverable，直到 successor 关闭首个 clean comparable outcome 且无直接 handoff-linked regression；此后才接受 rotation。Capability/transport defect 不等于 role regression；普通实现缺陷也不得追溯成 handoff regression。

不得把 active tool、external wait、新发现的必要事实、open-ended architecture analysis 或仍有有效输出的 bounded turn 判为 stall。只有 required reads 完成、无工具或外部结果在途、无结果/BLOCKED/新事实且 runtime watchdog 已过，才可触发恢复。

Context experiment 永远不是业务治理系统：metrics 必须 repository-external、content-free、append-only 且 non-authoritative；实验不得选择、拆分、延迟、替换业务任务，也不得改变业务 route、安全规则、模型或完成层。Rotation、compact hook 与 handoff automation 只可作为用户明确授权、非关键且有成本上限的研究，不是默认路线；普通业务不得为了采样或机制建设进入控制台 transport。

## 按触发条件完整读取 references

当下列触发条件成立时，先完整读取对应 reference，再规划或执行；读取失败时返回精确 BLOCKED，不凭常识重建协议：

- 在规划、执行或修改 compaction、bounded state、fresh handoff/rotation、persisted Goal、runtime transport、permission/capability correction、context measurement、cohort 或 rollback 前，读取 [Context Lifecycle and Runtime Metrics](references/context-lifecycle-and-runtime-metrics.md)。
- 在 opening/changing/pausing/splitting/closing outcome batch、ready-lane dispatch/re-dispatch、选择 concurrency/serialization、定义或复用 verification budget、执行 checkpoint-driven LIVENESS_RECHECK、进入 bounded Architect execution、判断 material Supervisor event 或 gate-close finding reconciliation 前，读取 [Outcome Batching and Review Budget](references/outcome-batching-and-review-budget.md)。
- 当 candidate 可能影响 protected semantic invariant，或准备、签发、消费、增量复核、判 stale 的 TECH_CLEAR/TECH_BLOCKED 前，读取 [Risk-Triggered Technical Review](references/technical-review-workflow.md)。普通低风险 NOT_REQUIRED 判断不要求重复加载。
- 在给 browser、desktop、device、account 或 remote session 分配 executable owner、启动 helper/keepalive、首个 executable thin slice 形成后准备扩展第二条依赖分支、执行首个 representative real-surface probe、判断 interactive USER_WAIT，或 pause/fail/cleanup runtime 前，读取 [Interactive Runtime Lifecycle](references/interactive-runtime-lifecycle.md)。
- 在长期 workflow 首次建立 intermediate user reporting、改变 reporting boundary、从内部 lifecycle 组成 cadence/milestone update、审计 communication health 或发 communication YELLOW 前，读取 [User Reporting Boundaries and Batching](references/user-reporting-boundaries.md)。
- 在打开 material event review、创建或回应 actionable Supervisor finding、改变 finding state 或 gate-close reconciliation 前，读取 [Architect-Supervisor Exchange Templates](references/review-exchange-templates.md) 并使用相应 bounded form。普通健康 heartbeat 不加载完整模板。

## 拒绝反模式并干净停止

拒绝以下行为：把 busy/commit/test/thread count 当业务进展；用 state card 代替当前事实；无 checkpoint 的无限 ACTIVE_WORK；Supervisor 变成第二 Architect 或 routine reviewer；为每个 candidate 强制 review；重复测试、订单、真实动作或证明链；用低层结果宣称高层完成；无必要的 approval、report、hash、manifest、签名或固定回复；局部 blocker 冻结无关安全工作；快速轮询和 mid-task micromanagement。

当 workflow 完成、用户暂停，或没有长期 target 时停止 heartbeat/monitor。返回最终 gate、最高 completion layer、任何未确认 handoff 与 OPEN finding；不要留下无目标的 recurring monitor。
