# BBBS 与 Live 小范围稳定性优化任务书

## 背景与已确认现状（不要重做）
- 项目：`/data/Bloret-Launcher`，当前分支 `Windows`，工作区初始干净，最近提交为 `bcfdf28`。
- BBBS 后端入口：`modules/bbbs.py`；Backend 薄封装在 `Bloret-Launcher.py:4453-4532`；页面为 `qml/pages/BBBS.qml`。
- Live 后端入口：`modules/bbbs_live.py`；Backend 入口约在 `Bloret-Launcher.py:4534-5020+`；页面为 `qml/pages/Live.qml`。
- 当前已存在 TTL 缓存、SSE 重连、Live/EasyTier 状态与聊天 UI，不要重写架构，不要碰 Passport 登录流程、EasyTier 核心实现或无关模块。
- `test_live_i18n.py` 是现有测试；仓库没有现成 BBBS/Live API 单测，需要补充针对本任务的无 GUI 单测。

## 目标
在不扩大功能范围的前提下，提升 BBBS 与 Live 的网络健壮性、隐私安全和并发一致性。优先修复真实可见的可靠性问题：Live SSE 停止可能无法及时退出/重连线程，旧的异步加入请求可能覆盖新状态，Live 调试日志会完整打印 cookies，BBBS/Live API 对异常响应和返回数据形状缺少统一防护。

## 需求清单
1. **Live SSE 生命周期与解析稳定性**（`modules/bbbs_live.py`）
   - 为 `LiveSSEClient` 增加可等待/可中断的停止机制：`stop()` 必须让读取循环尽快退出，避免旧线程在离开或切换空间后继续回调；不要引入永久阻塞的 join。
   - 保持 SSE 标准兼容：支持 `data:` 多行、事件结束时 flush、CRLF、注释/keep-alive 行；JSON 非法时只记录并继续，不让整个客户端永久退出。
   - 重连等待必须可被 stop 中断；避免多个 start 产生失控线程（start 幂等或先停止旧线程）。
   - 不能改变现有回调 payload 的主要字段语义。

2. **Live 并发/过期事件防护**（`Bloret-Launcher.py`，必要时 `modules/bbbs_live.py`）
   - 加入空间、离开空间、切换空间时，旧 SSE/旧异步请求的事件不得污染当前空间；至少以 space_id/客户端代次校验回调。
   - `sendLiveChatMessage` 在未加入空间、空消息、超长消息时应快速拒绝并给出已有 `liveErrorOccurred`，不能向 `None` 发送请求。
   - 不要破坏现有 QML 信号名和调用方式。

3. **隐私与日志安全**（`modules/bbbs_live.py`）
   - `_log_request` 禁止输出 session/session.sig 等 cookie 明文；保留方法、URL、非敏感 body 诊断信息。不要通过“关闭全部日志”掩盖问题。
   - 响应日志不得无界输出；保留截断后的诊断。

4. **BBBS/Live HTTP 响应防护**（`modules/bbbs.py`、`modules/bbbs_live.py`）
   - 对 JSON 解析失败、非 dict/list 返回、异常状态码统一安全处理，调用方继续得到既有约定的 `None`/`[]`/错误 payload，不因 `response.json()` 或 `result.get()` 崩溃。
   - 不要新增第三方依赖；复用 requests 和现有 log。

5. **补测试**
   - 新增一个无 GUI 的测试文件（建议 `test_bbbs_live.py`），使用 fake response/session/stream，不访问真实网络。
   - 至少覆盖：cookie 脱敏；SSE 多行 data/CRLF/keep-alive 与非法 JSON后继续；stop 能结束重连等待或读取；BBBS 非 JSON/错误状态的安全返回；空消息/未入房间校验（若放在 Backend 难以导入，可测试可复用的模块级辅助函数）。
   - 测试应能在无 PySide6 环境下运行；不要把重型 GUI import 放进测试。

## 技术与代码约束
- 新逻辑优先放服务/模块，`Bloret-Launcher.py` 只做必要薄修复；不要继续堆无关 Backend 方法。
- 不要修改 `server/store/passport`、`modules/easytier.py`、RinUI 子模块、配置文件、用户数据。
- 不要删除现有功能，不要重置或覆盖工作区已有改动（若发现新改动，保留并只改本任务相关文件）。
- 不要 push，不要调用其他模型；可以在当前仓库创建一个 commit。
- 兼容 Python 3.9+；避免依赖 Qt。

## 验证清单
1. `python3 -m py_compile modules/bbbs.py modules/bbbs_live.py test_bbbs_live.py`。
2. `python3 -m unittest -v test_bbbs_live.py test_live_i18n.py`。
3. 如改动 QML，运行仓库已有可用的 QML/语法检查；至少确认 diff 中 QML 无明显语法错误。
4. `git diff --check`。
5. `git diff --stat` 与 `git diff` 审查：只允许 BBBS/Live 相关文件和本任务测试/任务书。

## 输出要求
完成后在终端输出：改动文件清单、每项验证命令及真实结果、遗留问题。允许 commit 但禁止 push。不要只根据自述判断完成，交接后由主代理复核真实 diff 和测试。
