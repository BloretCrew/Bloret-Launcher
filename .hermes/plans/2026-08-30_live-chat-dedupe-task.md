# 络聊 Live 聊天可靠性优化任务书

## 背景与已确认现状（不要重做）
- 仓库：`/data/Bloret-Launcher`，当前分支为 `Windows`；已有用户未跟踪目录 `.hermes/`，不要删除、重置或覆盖其中其他内容。
- 当前 Live 聊天链路：`qml/pages/Live.qml` 的 `chatInput` 调用 `Backend.sendLiveChatMessage`；`Bloret-Launcher.py` 通过 `modules.bbbs_live.send_signal()` POST `/api/live/signal/:spaceId`；实时消息由 `LiveSSEClient` 订阅 `/api/live/events/:spaceId`，经 `_handle_live_event` 发 `liveChatMessageReceived`。
- 已有 `validate_chat_message`、SSE 重连/解析、消息 `msgId` 生成、初始历史规范化和相关测试 `test_bbbs_live.py`。不要重写 BBS/Live 或 EasyTier，不要改服务器端。
- 当前已确认的风险：发送成功后 Backend 在 `sendLiveChatMessage` 立即本地 append + emit 一次；服务器通常又会通过 SSE 广播同一条 chat，`_handle_live_event` 无去重，可能导致发送者看到重复消息。历史消息与实时消息也缺少统一的 msgId 去重边界。

## 目标范围
只修 Live 络聊消息的重复/乱序可靠性，不扩展到音视频、EasyTier、BBBS 帖子、PassPort 登录或服务端 API。

## 实现要求
1. 优先在 `modules/services/` 放纯业务逻辑；但本任务若现有 Live 逻辑集中于 `modules/bbbs_live.py` + Backend，可新增轻量、无 GUI 依赖的聊天去重/规范化 helper（例如 `modules/services/live_chat.py`），由 `Bloret-Launcher.py` 薄调用。不要继续无脑新增大型逻辑到 `Bloret-Launcher.py`。
2. 为 chat 事件提供稳定、可测试的去重策略：优先使用 `payload.msgId`（兼容事件顶层 `msgId`）；没有 msgId 时不要把所有同文消息误判为重复，至少使用保守策略。去重应覆盖：初始 `chatHistory`、发送成功的本地回显、SSE 回显；不要无限增长内存，设合理上限或随历史裁剪。
3. 发送成功后的 UI 不能重复显示服务器 SSE 回显；同时不能因为 SSE 到达稍晚而丢失正常消息。保留当前异步发送、错误提示、插件 hook 语义。
4. `_normalize_live_chat_history`、`_handle_live_event`、`sendLiveChatMessage` 相关改动必须兼容现有服务端字段（`from`/`msg`/`message`/`payload`、`recalled`、`time`、`msgId`），不能破坏 QML 现有 `resolveChatText`。
5. 若需要更新 QML，只做必要的小改动（例如稳定 key/滚动行为），不要重做 Live 页面。
6. 不泄漏 session cookie、密码或其他认证信息；不要降低现有请求校验与日志脱敏。

## 验证清单（必须实际运行并记录结果）
- `python3 -m py_compile modules/bbbs_live.py Bloret-Launcher.py`（如新增 Python 文件一并加入）。
- `python3 -m unittest -v test_bbbs_live.py`。
- 为去重/规范化补充单元测试，至少覆盖：
  - 同一 `msgId` 的本地回显 + SSE 事件只保留一条；
  - 不同 `msgId` 但相同文本的两条消息都保留；
  - 初始历史中重复 msgId 被裁剪；
  - 缺失 msgId 的消息不会因文本相同被错误全部吞掉；
  - 现有发送校验和 SSE 测试继续通过。
- 如仓库存在针对 Live/络聊的其他测试，运行相关测试；不要声称运行了不存在的测试。
- 检查 `git diff --check`，并审阅真实 diff，确认没有无关改动。

## 禁止事项
- 禁止修改服务端、数据库、Passport 登录逻辑、`modules/web.py`、EasyTier 或无关 QML。
- 禁止删除用户数据、reset/checkout 覆盖现有改动、push 远端。
- 禁止把认证 cookie/token 写入日志或测试输出。
- 禁止引入 PySide6 到纯逻辑 helper，保证测试可脱离 GUI import。

## 输出要求
- 允许在当前仓库创建一个清晰的 commit，但不要 push；不要提交与本任务无关的已有用户改动或 `.hermes/` 任务书（除非明确需要，默认任务书不纳入 commit）。
- 最终输出：改动文件清单、核心行为、实际验证命令及结果、commit hash、遗留问题。
- 先阅读本任务书和当前工作区，再实现；不要只给方案，必须落地并验证。
