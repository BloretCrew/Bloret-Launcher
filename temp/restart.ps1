# 停止正在运行的 Bloret-Launcher 进程
Stop-Process -Name "Bloret-Launcher" -Force -ErrorAction SilentlyContinue

# 等待一段时间确保进程完全终止
# Start-Sleep -Seconds 1

# 启动新的 Bloret-Launcher 实例
Start-Process -FilePath "Bloret-Launcher.exe"