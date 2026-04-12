实施计划

我会按“先打通 Live 内联机闭环，再补细节”的顺序做，先不改代码，等你审批后开始。

梳理并重构 EasyTier 运行层
把现有 modules/easytier.py 从旧的“独立联机入口”改成可被 Live 调用的会话管理器。
目标是统一支持：
房主启动 EasyTier 网络
成员加入同一 Live 后连接房主网络
进程生命周期管理：加入、离开、关闭启动器时都能正确停掉 easytier-core
按文档改成免提权主流程：--no-tun + 本地代理端口 + 读取虚拟 IP。
顺手修正当前实现里比较旧、偏 Windows-only 的写法，至少保证现在仓库这套 Windows 发行物能稳定跑通。
扩展 BBBS Live 服务端状态模型
在 temp/BBBS/server.js 的 liveSpaces 中新增 easytier 状态，字段大致会包括：
enabled
hostUsername
networkName
networkSecret
hostVirtualIp
gamePort
status
startedAt
保持 Live 现有“内存态房间”风格，不额外落库。
增加 EasyTier 专用接口，供启动器调用：
房主开启/关闭 EasyTier
房主上报虚拟 IP 与局域网端口
房间成员查询当前 EasyTier 状态
同时把 EasyTier 状态变化通过 SSE 广播到同一个 Live 里，避免轮询。
把 EasyTier 集成进 Live 客户端链路
扩展 modules/bbbs_live.py，补 EasyTier 相关 API 调用。
扩展 Bloret-Launcher.py 的 Backend，新增 Live 内 EasyTier 槽函数和信号。
目标交互：
房主进入 Live 后，可点击“开始 EasyTier 网络”
网络名固定为 BLEASYTIER<用户名>
成员进入同一个 Live 后，可点击“连接房主网络”
不再要求用户手填网络名、密钥、房主 IP
做房主侧联机闭环
房主点击开始后：
本地启动 EasyTier
服务端记录网络元数据
启动器开始监听 Minecraft latest.log
当房主在游戏里“对局域网开放”后：
自动抓取端口
读取本机 EasyTier 虚拟 IP
上报到当前 Live
这样 Live 内其他成员就能拿到最终目标地址 虚拟IP:端口。
做加入者侧联机闭环
成员点击连接后：
本地启动 EasyTier 加入同一网络
启动本地 SOCKS5 代理
将房主地址自动写入对应版本的 servers.dat
启动游戏时自动注入 JVM 代理参数：
-DsocksProxyHost=127.0.0.1
-DsocksProxyPort=<proxyPort>
-DsocksNonProxyHosts=localhost|127.0.0.1
-Djava.net.preferIPv4Stack=true
这样成员进入多人游戏后，能直接看到 Live 对应的房间。
调整 Live 页面 UI
在 qml/pages/Live.qml 里新增 EasyTier 区块，嵌进当前 Live 内页，而不是单独做旧联机入口。
房主视角显示：
开始网络
等待开放局域网
当前虚拟 IP / 端口 / 状态
成员视角显示：
房主是否已开启网络
是否已捕获端口
连接按钮
必要提示，比如“请通过启动器启动游戏以注入代理”
启动与退出时的收尾
离开 Live、房主关闭网络、启动器退出时，统一清理 EasyTier 进程。
避免把代理状态永久污染到普通启动流程。
房主离开 Live 时，服务端自动清空当前房间的 EasyTier 状态，并广播给其他成员。
验证与回归
我会至少验证这几条：
房主在 Live 内能一键开启 EasyTier
房主开放局域网后，端口能被自动抓到并同步到 Live
成员进入同一 Live 后能一键连接
成员启动游戏后能在多人游戏里看到自动写入的服务器
离开 Live 后 EasyTier 进程被正确关闭
原有 Live 聊天/SSE 不被破坏
预计涉及文件

modules/easytier.py
modules/bbbs_live.py
modules/launch.py
Bloret-Launcher.py
qml/pages/Live.qml
temp/BBBS/server.js
我建议默认采用的两个约束

先按当前仓库现状把 Windows 主流程 做通；跨平台结构会预留，但这次不把 macOS/Linux 二进制分发一起做完。
因为网络名固定为 BLEASYTIER<用户名>，同一用户名同一时间只允许一个 Live 开启 EasyTier 网络，避免冲突。