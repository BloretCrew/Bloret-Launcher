'=================================================================================
' ModDownload 模块 - Minecraft 下载相关功能的主模块
' 该模块包含了所有与 Minecraft 客户端、支持库、资源文件等下载相关的功能
'=================================================================================
Public Module ModDownload

#Region "DlClient* | Minecraft 客户端"

    ''' <summary>
    ''' 获取指定 Minecraft 版本的主 Jar 文件下载信息
    ''' 该函数会处理版本继承链，检查文件完整性，并返回下载所需的所有信息
    ''' 失败则抛出异常，如果文件已存在且完整则返回 Nothing
    ''' </summary>
    ''' <param name="Version">Minecraft 版本对象，包含版本的所有信息</param>
    ''' <param name="ReturnNothingOnFileUseable">如果文件已存在且可用，是否返回 Nothing 而不是下载信息</param>
    ''' <returns>NetFile 对象，包含下载地址、本地路径和文件校验信息，如果文件已存在且完整则返回 Nothing</returns>
    Public Function DlClientJarGet(Version As McVersion, ReturnNothingOnFileUseable As Boolean) As NetFile
        '=================================================================================
        ' 第一步：解析版本继承链
        ' 有些版本是继承自其他版本的（如 Forge 版本继承自原版）
        ' 需要找到最底层的原版版本才能获取正确的下载信息
        '=================================================================================
        Try
            ' 使用循环处理多层继承关系
            ' 例如：1.12.2-Forge 可能继承自 1.12.2，而 1.12.2 可能又继承自其他版本
            Do While Not String.IsNullOrEmpty(Version.InheritVersion)
                ' 创建新的 McVersion 对象来获取继承版本的信息
                Version = New McVersion(Version.InheritVersion)
            Loop
        Catch ex As Exception
            ' 记录继承链解析失败的错误，但继续执行后续逻辑
            Log(ex, "获取底层继承版本失败")
        End Try
        
        '=================================================================================
        ' 第二步：验证版本 JSON 数据完整性
        ' 确保版本 JSON 中包含必要的下载信息字段
        '=================================================================================
        ' 检查 JSON 结构中是否包含 downloads 字段
        If Version.JsonObject("downloads") Is Nothing OrElse 
           ' 检查 downloads 中是否包含 client 字段
           Version.JsonObject("downloads")("client") Is Nothing OrElse 
           ' 检查 client 中是否包含 url 下载地址字段
           Version.JsonObject("downloads")("client")("url") Is Nothing Then
            ' 如果缺少必要的下载信息，抛出异常
            Throw New Exception("底层版本 " & Version.Name & " 中无 jar 文件下载信息")
        End If
        
        '=================================================================================
        ' 第三步：创建文件校验器
        ' 用于验证本地文件是否完整，避免重复下载
        '=================================================================================
        ' 创建 FileChecker 对象，设置文件最小大小为 1KB
        ' 从 JSON 中获取文件的实际大小和 SHA1 哈希值用于校验
        Dim Checker As New FileChecker(MinSize:=1024, 
                                     ActualSize:=If(Version.JsonObject("downloads")("client")("size"), -1), 
                                     Hash:=Version.JsonObject("downloads")("client")("sha1"))
        
        '=================================================================================
        ' 第四步：检查本地文件是否可用
        ' 如果文件已存在且通过校验，根据参数决定是否返回 Nothing
        '=================================================================================
        ' 如果参数要求文件可用时返回 Nothing，且文件确实通过了校验
        If ReturnNothingOnFileUseable AndAlso Checker.Check(Version.Path & Version.Name & ".jar") Is Nothing Then 
            Return Nothing ' 文件已存在且完整，无需下载
        End If
        
        '=================================================================================
        ' 第五步：构造并返回下载信息
        ' 包含下载地址、本地保存路径和文件校验信息
        '=================================================================================
        ' 从 JSON 中获取 Jar 文件的下载地址
        Dim JarUrl As String = Version.JsonObject("downloads")("client")("url")
        ' 创建 NetFile 对象，包含下载源、本地路径和校验信息
        Return New NetFile(DlSourceLauncherOrMetaGet(JarUrl), Version.Path & Version.Name & ".jar", Checker)
    End Function

    ''' <summary>
    ''' 获取指定 Minecraft 版本的资源文件索引(AssetIndex)下载信息
    ''' 资源文件索引包含了该版本所有资源文件（音效、语言文件等）的列表和哈希信息
    ''' 如果未找到索引信息，则返回 Legacy 资源文件或 Nothing
    ''' </summary>
    ''' <param name="Version">Minecraft 版本对象</param>
    ''' <returns>NetFile 对象，包含资源索引文件的下载信息，如果无法获取则返回 Nothing</returns>
    Public Function DlClientAssetIndexGet(Version As McVersion) As NetFile
        '=================================================================================
        ' 第一步：解析版本继承链
        ' 与 Jar 文件类似，需要找到最底层的原版版本
        ' 因为资源文件索引信息存储在底层原版版本中
        '=================================================================================
        ' 使用循环处理多层继承关系，直到找到最底层的原版版本
        Do While Not String.IsNullOrEmpty(Version.InheritVersion)
            ' 创建新的 McVersion 对象来获取继承版本的信息
            Version = New McVersion(Version.InheritVersion)
        Loop
        
        '=================================================================================
        ' 第二步：获取资源文件索引信息
        ' 调用 McAssetsGetIndex 函数从版本 JSON 中提取资源索引信息
        '=================================================================================
        ' 获取资源索引信息，包含索引 ID 和下载地址
        ' 参数 True, True 表示允许使用缓存和允许回退到 Legacy 资源
        Dim IndexInfo = McAssetsGetIndex(Version, True, True)
        
        '=================================================================================
        ' 第三步：构造本地文件路径
        ' 资源索引文件保存在 .minecraft/assets/indexes/ 目录下
        '=================================================================================
        ' 构造资源索引文件的本地保存路径
        ' 格式：.minecraft/assets/indexes/{索引ID}.json
        Dim IndexAddress As String = PathMcFolder & "assets\indexes\" & IndexInfo("id").ToString & ".json"
        ' 记录日志，显示当前版本对应的资源索引 ID
        Log("[Download] 版本 " & Version.Name & " 对应的资源文件索引为 " & IndexInfo("id").ToString)
        
        '=================================================================================
        ' 第四步：检查并返回下载信息
        ' 如果存在下载地址则返回 NetFile 对象，否则返回 Nothing
        '=================================================================================
        ' 从索引信息中获取下载地址，如果不存在则使用空字符串
        Dim IndexUrl As String = If(IndexInfo("url"), "")
        ' 检查是否有可用的下载地址
        If IndexUrl = "" Then
            ' 没有下载地址，返回 Nothing
            Return Nothing
        Else
            ' 有下载地址，创建 NetFile 对象
            ' CanUseExistsFile:=False 表示不检查本地文件是否存在，总是重新下载
            ' IsJson:=True 表示这是一个 JSON 文件，需要进行 JSON 格式验证
            Return New NetFile(DlSourceLauncherOrMetaGet(IndexUrl), IndexAddress, New FileChecker(CanUseExistsFile:=False, IsJson:=True))
        End If
    End Function

    ''' <summary>
    ''' 构造补全指定 Minecraft 版本所需的所有文件的加载器列表
    ''' 该函数会创建下载支持库文件和资源文件的完整加载器链
    ''' 支持自定义资源文件索引更新行为，失败会抛出异常
    ''' </summary>
    ''' <param name="Version">Minecraft 版本对象</param>
    ''' <param name="CheckAssetsHash">是否检查资源文件的哈希值，确保文件完整性</param>
    ''' <param name="AssetsIndexBehaviour">资源文件索引存在时的处理行为枚举值</param>
    ''' <returns>包含所有必要加载器的列表，按执行顺序排列</returns>
    Public Function DlClientFix(Version As McVersion, CheckAssetsHash As Boolean, AssetsIndexBehaviour As AssetsIndexExistsBehaviour) As List(Of LoaderBase)
        '=================================================================================
        ' 初始化加载器列表
        ' 该列表将包含所有需要执行的加载器，按执行顺序排列
        '=================================================================================
        Dim Loaders As New List(Of LoaderBase)

        '=================================================================================
        ' 第一部分：支持库文件下载
        ' 支持库是 Minecraft 运行所需的各种依赖库文件
        '=================================================================================
#Region "下载支持库文件"
        ' 创建支持库下载的子加载器列表
        Dim LoadersLib As New List(Of LoaderBase) From {
            ' 第一个加载器：分析缺失的支持库文件
            ' 调用 McLibFix 函数检查哪些支持库需要下载
            New LoaderTask(Of String, List(Of NetFile))("分析缺失支持库文件", Sub(Task As LoaderTask(Of String, List(Of NetFile))) Task.Output = McLibFix(Version)) With {.ProgressWeight = 1},
            ' 第二个加载器：实际下载支持库文件
            ' 使用上一步分析出的文件列表进行下载
            New LoaderDownload("下载支持库文件", New List(Of NetFile)) With {.ProgressWeight = 15}
        }
        ' 将支持库下载子加载器包装成组合加载器并添加到主列表
        ' Block = False 表示不阻塞主线程，Show = False 表示不显示详细进度
        Loaders.Add(New LoaderCombo(Of String)("下载支持库文件（主加载器）", LoadersLib) With {.Block = False, .Show = False, .ProgressWeight = 16})
#End Region

        '=================================================================================
        ' 第二部分：资源文件下载
        ' 资源文件包括游戏音效、语言文件、图标等
        '=================================================================================
#Region "下载资源文件"
        ' 检查是否应该跳过资源文件检查（如某些特殊版本）
        If ShouldIgnoreFileCheck(Version) Then
            ' 跳过资源文件检查，记录日志
            Log("[Download] 已跳过所有 Assets 检查")
        Else
            ' 创建资源文件下载的子加载器列表
            Dim LoadersAssets As New List(Of LoaderBase)
            
            '---------------------------------------------------------------------------------
            ' 子加载器 1：分析资源文件索引地址
            ' 确定需要下载的资源索引文件
            '---------------------------------------------------------------------------------
            LoadersAssets.Add(New LoaderTask(Of String, List(Of NetFile))("分析资源文件索引地址",
            Sub(Task As LoaderTask(Of String, List(Of NetFile)))
                Try
                    ' 调用 DlClientAssetIndexGet 获取资源索引文件信息
                    Dim IndexFile = DlClientAssetIndexGet(Version)
                    Dim IndexFileInfo As New FileInfo(IndexFile.LocalPath)
                    ' 根据 AssetsIndexBehaviour 参数决定是否需要下载索引文件
                    If AssetsIndexBehaviour <> AssetsIndexExistsBehaviour.AlwaysDownload AndAlso IndexFile.Check.Check(IndexFile.LocalPath) Is Nothing Then
                        ' 文件已存在且完整，无需下载，返回空列表
                        Task.Output = New List(Of NetFile)
                    Else
                        ' 需要下载索引文件，返回包含该文件的列表
                        Task.Output = New List(Of NetFile) From {IndexFile}
                    End If
                Catch ex As Exception
                    ' 索引地址分析失败，包装异常并重新抛出
                    Throw New Exception("分析资源文件索引地址失败", ex)
                End Try
            End Sub) With {.ProgressWeight = 0.5, .Show = False})
            
            '---------------------------------------------------------------------------------
            ' 子加载器 2：下载资源文件索引
            ' 使用上一步分析出的文件列表进行下载
            '---------------------------------------------------------------------------------
            LoadersAssets.Add(New LoaderDownload("下载资源文件索引", New List(Of NetFile)) With {.ProgressWeight = 2})
            
            '---------------------------------------------------------------------------------
            ' 后台更新资源文件索引（可选）
            ' 当 AssetsIndexBehaviour 为 DownloadInBackground 时启用
            '---------------------------------------------------------------------------------
            If AssetsIndexBehaviour = AssetsIndexExistsBehaviour.DownloadInBackground Then
                ' 创建后台更新的子加载器列表
                Dim LoadersAssetsUpdate As New List(Of LoaderBase)
                ' 临时变量，用于存储临时文件路径和真实文件路径
                Dim TempAddress As String = Nothing
                Dim RealAddress As String = Nothing
                
                LoadersAssetsUpdate.Add(New LoaderTask(Of String, List(Of NetFile))("后台分析资源文件索引地址",
                Sub(Task As LoaderTask(Of String, List(Of NetFile)))
                    ' 获取资源索引文件信息
                    Dim BackAssetsFile As NetFile = DlClientAssetIndexGet(Version)
                    ' 保存真实文件路径
                    RealAddress = BackAssetsFile.LocalPath
                    ' 构造临时文件路径（在临时目录的 Cache 子目录中）
                    TempAddress = PathTemp & "Cache\" & BackAssetsFile.LocalName
                    ' 修改下载目标为临时路径
                    BackAssetsFile.LocalPath = TempAddress
                    Task.Output = New List(Of NetFile) From {BackAssetsFile}
                    '---------------------------------------------------------------------------------
                    ' 检查是否需要更新：每天只更新一次
                    ' 通过比较文件的最后修改时间和当前日期来判断
                    '---------------------------------------------------------------------------------
                    If File.Exists(RealAddress) AndAlso Math.Abs((File.GetLastWriteTime(RealAddress).Date - Now.Date).TotalDays) < 1 Then
                        ' 文件在一天内已更新过，无需重复更新
                        Log("[Download] 无需更新资源文件索引，取消")
                        Task.Abort() ' 中止任务执行
                    End If
                End Sub))
                
                ' 后台下载资源文件索引
                LoadersAssetsUpdate.Add(New LoaderDownload("后台下载资源文件索引", New List(Of NetFile)))
                
                ' 后台复制资源文件索引
                LoadersAssetsUpdate.Add(New LoaderTask(Of List(Of NetFile), String)("后台复制资源文件索引",
                Sub(Task As LoaderTask(Of List(Of NetFile), String))
                    ' 将临时文件复制到真实位置
                    CopyFile(TempAddress, RealAddress)
                    ' 记录后台更新成功的日志
                    McLaunchLog("后台更新资源文件索引成功：" & TempAddress)
                End Sub))
                
                ' 创建后台更新的组合加载器
                Dim Updater As New LoaderCombo(Of String)("后台更新资源文件索引", LoadersAssetsUpdate)
                Log("[Download] 开始后台检查资源文件索引")
                ' 启动后台更新任务，不阻塞主流程
                Updater.Start()
            End If
            
            '---------------------------------------------------------------------------------
            ' 子加载器 3：分析缺失的资源文件
            ' 根据资源索引文件分析哪些具体的资源文件需要下载
            '---------------------------------------------------------------------------------
            LoadersAssets.Add(New LoaderTask(Of String, List(Of NetFile))("分析缺失资源文件",
            Sub(Task As LoaderTask(Of String, List(Of NetFile)))
                ' 调用 McAssetsFixList 分析缺失的资源文件
                ' CheckAssetsHash 参数控制是否检查文件哈希值
                Task.Output = McAssetsFixList(Version, CheckAssetsHash, Task)
            End Sub) With {.ProgressWeight = 3})
            
            '---------------------------------------------------------------------------------
            ' 子加载器 4：下载资源文件
            ' 使用上一步分析出的文件列表进行下载
            '---------------------------------------------------------------------------------
            LoadersAssets.Add(New LoaderDownload("下载资源文件", New List(Of NetFile)) With {.ProgressWeight = 25})
            
            '---------------------------------------------------------------------------------
            ' 将资源文件下载子加载器包装成组合加载器
            '---------------------------------------------------------------------------------
            Loaders.Add(New LoaderCombo(Of String)("下载资源文件（主加载器）", LoadersAssets) With {.Block = False, .Show = False, .ProgressWeight = 30.5})
        End If
#End Region

        '=================================================================================
        ' 返回完整的加载器列表
        ' 列表中的加载器将按顺序执行，完成版本文件的补全
        '=================================================================================
        Return Loaders
    End Function
    '=================================================================================
    ' 资源文件索引存在时的处理行为枚举
    ' 用于控制当资源文件索引已存在时的不同处理策略
    '=================================================================================
    Public Enum AssetsIndexExistsBehaviour
        ''' <summary>
        ''' 如果文件存在，则不进行下载。
        ''' 适用于希望节省带宽，不频繁更新索引的场景
        ''' </summary>
        DontDownload
        ''' <summary>
        ''' 如果文件存在，则启动新的下载加载器进行独立的更新。
        ''' 在后台异步更新，不影响主流程，适用于需要保持索引相对最新的场景
        ''' </summary>
        DownloadInBackground
        ''' <summary>
        ''' 如果文件存在，也同样进行下载。
        ''' 强制重新下载，确保获取最新版本，适用于需要绝对最新索引的场景
        ''' </summary>
        AlwaysDownload
    End Enum

#End Region

#Region "DlClientList | Minecraft 客户端 版本列表"

    '主加载器
    ''' <summary>
    ''' Minecraft 客户端版本列表结果结构体。
    ''' 用于存储从不同下载源获取到的版本列表数据，包含数据来源信息和JSON内容。
    ''' </summary>
    Public Structure DlClientListResult
        ''' <summary>
        ''' 数据来源名称，如“Mojang”，“BMCLAPI”。
        ''' 用于标识当前版本列表数据来自哪个下载源，便于用户了解数据来源和选择合适的下载源。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' True表示数据来自Mojang官方源，False表示来自第三方镜像源如BMCLAPI。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 获取到的 Json 数据。
        ''' 包含完整的版本列表信息，包括版本ID、类型、发布时间、下载地址等元数据。
        ''' </summary>
        Public Value As JObject
        '''' <summary>
        '''' 官方源的失败原因。若没有则为 Nothing。
        '''' 用于记录官方源下载失败的具体异常信息，便于调试和错误处理。
        '''' </summary>
        'Public OfficialError As Exception
    End Structure
    ''' <summary>
    ''' Minecraft 客户端版本列表主加载器。
    ''' 作为版本列表获取的统一入口，根据用户设置选择不同的下载源策略，管理多个子加载器的执行顺序和超时时间。
    ''' 若要求镜像源必须包含某个版本，则将该版本 ID 作为输入（#5195）。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，包含输入参数和状态管理</param>
    ''' <remarks>
    ''' 下载源策略说明：
    ''' - Case 0: 优先使用BMCLAPI（30秒超时），失败后尝试Mojang官方源（90秒超时）
    ''' - Case 1: 优先使用Mojang官方源（5秒超时），失败后尝试BMCLAPI（35秒超时）
    ''' - Case Else: 仅使用Mojang官方源（60秒超时），失败后尝试BMCLAPI（120秒超时）
    ''' </remarks>
    Public DlClientListLoader As New LoaderTask(Of String, DlClientListResult)("DlClientList Main", AddressOf DlClientListMain)
    Private Sub DlClientListMain(Loader As LoaderTask(Of String, DlClientListResult))
        '根据用户设置选择下载源策略
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                '策略0：优先使用镜像源，降低官方源压力
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListBmclapiLoader, 30),      'BMCLAPI源，30秒超时
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListMojangLoader, 30 + 60)  'Mojang官方源，90秒超时（30+60）
                }, Loader.IsForceRestarting)
            Case 1
                '策略1：优先使用官方源，获取最新数据
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListMojangLoader, 5),        'Mojang官方源，5秒超时
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListBmclapiLoader, 5 + 30)    'BMCLAPI源，35秒超时（5+30）
                }, Loader.IsForceRestarting)
            Case Else
                '策略2：仅使用官方源，确保数据准确性
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListMojangLoader, 60),       'Mojang官方源，60秒超时
                    New KeyValuePair(Of LoaderTask(Of String, DlClientListResult), Integer)(DlClientListBmclapiLoader, 60 + 60) 'BMCLAPI源，120秒超时（60+60）
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    '各个下载源的分加载器
    ''' <summary>
    ''' Minecraft 客户端版本列表，Mojang官方源加载器。
    ''' 负责从Mojang官方API获取Minecraft版本列表，处理版本数据验证、网络性能检测、更新提示等功能。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，包含输入参数和状态管理</param>
    ''' <remarks>
    ''' 主要功能：
    ''' 1. 从官方API获取版本列表JSON数据
    ''' 2. 验证数据完整性（检查版本数量）
    ''' 3. 检测网络性能，决定是否优先使用官方源
    ''' 4. 添加PCL特供版本项
    ''' 5. 检测新版本并显示更新提示
    ''' 6. 记录最高版本号用于后续处理
    ''' </remarks>
    Public DlClientListMojangLoader As New LoaderTask(Of String, DlClientListResult)("DlClientList Mojang", AddressOf DlClientListMojangMain)
    Private IsNewClientVersionHinted As Boolean = False  '标记是否已经提示过新版本，避免重复提示
    Private Sub DlClientListMojangMain(Loader As LoaderTask(Of String, DlClientListResult))
        '记录开始时间，用于网络性能检测
        Dim StartTime As Long = GetTimeTick()
        '从Mojang官方API获取版本列表JSON数据，要求返回JSON格式
        Dim Json As JObject = GetJson(NetRequestByClientRetry("https://launchermeta.mojang.com/mc/game/version_manifest.json", RequireJson:=True))
        Try
            '获取版本数组并验证数据完整性
            Dim Versions As JArray = Json("versions")
            If Versions.Count < 200 Then Throw New Exception("获取到的版本列表长度不足（" & Json.ToString & "）")
            
            '确定官方源是否可用：通过响应时间判断网络质量
            If Not DlPreferMojang Then
                Dim DeltaTime = GetTimeTick() - StartTime
                DlPreferMojang = DeltaTime < 4000  '4秒内响应认为网络良好，可优先使用官方源
                Log($"[Download] Mojang 官方源加载耗时：{DeltaTime}ms，{If(DlPreferMojang, "可优先使用官方源", "不优先使用官方源")}")
            End If
            
            '添加PCL特供项：合并自定义版本信息（如果存在）
            If File.Exists(PathTemp & "Cache\download.json") Then Versions.Merge(GetJson(ReadFile(PathTemp & "Cache\download.json")))
            
            '返回结果：标记为官方数据，设置数据源名称
            Loader.Output = New DlClientListResult With {.IsOfficial = True, .SourceName = "Mojang 官方源", .Value = Json}
            
            '解析更新提示（Release版本）：检测是否有新的正式版本发布
            Dim Version As String = Json("latest")("release")
            If Setup.Get("ToolUpdateRelease") AndAlso Not Setup.Get("ToolUpdateReleaseLast") = "" AndAlso Version IsNot Nothing AndAlso Not Setup.Get("ToolUpdateReleaseLast") = Version Then
                McDownloadClientUpdateHint(Version, Json)  '显示新版本提示
                IsNewClientVersionHinted = True  '标记已提示，避免重复提示快照版本
            End If
            '记录最高版本号（取版本号的第二位，如1.20.1中的20）
            McVersionHighest = Version.Split(".")(1)
            Setup.Set("ToolUpdateReleaseLast", Version)  '更新最后记录的正式版本
            
            '解析更新提示（Snapshot版本）：检测是否有新的快照版本发布
            Version = Json("latest")("snapshot")
            If Setup.Get("ToolUpdateSnapshot") AndAlso Not Setup.Get("ToolUpdateSnapshotLast") = "" AndAlso Version IsNot Nothing AndAlso Not Setup.Get("ToolUpdateSnapshotLast") = Version AndAlso Not IsNewClientVersionHinted Then
                McDownloadClientUpdateHint(Version, Json)  '显示新版本提示（仅当未提示过正式版本时）
            End If
            Setup.Set("ToolUpdateSnapshotLast", If(Version, "Nothing"))  '更新最后记录的快照版本
        Catch ex As Exception
            Throw New Exception("Minecraft 官方源版本列表解析失败", ex)
        End Try
    End Sub
    ''' <summary>
    ''' Minecraft 客户端版本列表，BMCLAPI镜像源加载器。
    ''' 负责从BMCLAPI镜像源获取Minecraft版本列表，提供国内网络优化访问，处理版本数据验证和特定版本检查。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，包含输入参数和状态管理</param>
    ''' <remarks>
    ''' 主要功能：
    ''' 1. 从BMCLAPI镜像源获取版本列表JSON数据
    ''' 2. 验证数据完整性（检查版本数量）
    ''' 3. 添加PCL特供版本项
    ''' 4. 检查是否包含特定要求的版本（#5195）
    ''' 5. 返回非官方镜像源结果
    ''' </remarks>
    Public DlClientListBmclapiLoader As New LoaderTask(Of String, DlClientListResult)("DlClientList Bmclapi", AddressOf DlClientListBmclapiMain)
    Private Sub DlClientListBmclapiMain(Loader As LoaderTask(Of String, DlClientListResult))
        '从BMCLAPI镜像源获取版本列表JSON数据，要求返回JSON格式
        Dim Json As JObject = GetJson(NetRequestByClientRetry("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json", RequireJson:=True))
        Try
            '获取版本数组并验证数据完整性
            Dim Versions As JArray = Json("versions")
            If Versions.Count < 200 Then Throw New Exception("获取到的版本列表长度不足（" & Json.ToString & "）")
            
            '添加PCL特供项：合并自定义版本信息（如果存在）
            If File.Exists(PathTemp & "Cache\download.json") Then Versions.Merge(GetJson(ReadFile(PathTemp & "Cache\download.json")))
            
            '检查是否有要求的版本（#5195）：确保镜像源包含用户需要的特定版本
            If Not String.IsNullOrEmpty(Loader.Input) Then
                Dim Id = Loader.Input  '获取需要检查的版本ID
                '检查当前版本列表是否包含目标版本
                If DlClientListLoader.Output.Value IsNot Nothing AndAlso Not DlClientListLoader.Output.Value("versions").Any(Function(v) v("id") = Id) Then
                    Throw New Exception("BMCLAPI 源未包含目标版本 " & Id)  '版本不存在则抛出异常
                End If
            End If
            
            '返回结果：标记为非官方镜像数据，设置数据源名称
            Loader.Output = New DlClientListResult With {.IsOfficial = False, .SourceName = "BMCLAPI", .Value = Json}
        Catch ex As Exception
            Throw New Exception("Minecraft BMCLAPI 版本列表解析失败（" & Json.ToString & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' 获取指定Minecraft版本的JSON下载地址。
    ''' 根据版本ID从版本列表中查找对应的JSON元数据下载地址，处理版本ID格式标准化和多种状态情况。
    ''' 若失败则返回 Nothing。必须在工作线程执行。
    ''' </summary>
    ''' <param name="Id">Minecraft版本ID，如"1.20.1"、"23w31a"等</param>
    ''' <returns>版本JSON文件的下载URL，若未找到则返回Nothing</returns>
    ''' <remarks>
    ''' 处理流程：
    ''' 1. 版本ID格式标准化（处理下划线和多余的.0）
    ''' 2. 根据加载器状态选择不同的获取策略
    ''' 3. 在版本列表中查找匹配项
    ''' 4. 返回对应的JSON下载地址
    ''' </remarks>
    Public Function DlClientListGet(Id As String)
        Try
            '步骤1：确认版本格式标准，处理特殊情况
            Id = Id.Replace("_", "-") '1.7.10_pre4 在版本列表中显示为 1.7.10-pre4
            If Id <> "1.0" AndAlso Id.EndsWithF(".0") Then Id = Left(Id, Id.Length - 2) 'OptiFine 1.8 的下载会触发此问题，显示版本为 1.8.0
            
            '步骤2：根据加载器状态选择获取策略
            Select Case DlClientListLoader.State
                Case LoadState.Finished
                    '状态：已完成 - 从当前结果中查找目标版本
                    For Each Version As JObject In DlClientListLoader.Output.Value("versions")
                        If Version("id") = Id Then Return Version("url").ToString  '找到匹配版本，返回JSON下载地址
                    Next
                    '未找到目标版本，重新获取版本列表（在版本刚更新时可能出现这种情况，#5195）
                    DlClientListLoader.WaitForExit(Id, IsForceRestart:=True)
                Case LoadState.Loading
                    '状态：加载中 - 等待当前加载完成
                    DlClientListLoader.WaitForExit(Id)
                Case LoadState.Failed, LoadState.Aborted, LoadState.Waiting
                    '状态：失败/中止/等待 - 强制重新启动加载
                    DlClientListLoader.WaitForExit(Id, IsForceRestart:=True)
            End Select
            
            '步骤3：重新查找版本（等待加载完成后）
            For Each Version As JObject In DlClientListLoader.Output.Value("versions")
                If Version("id") = Id Then Return Version("url").ToString  '找到匹配版本，返回JSON下载地址
            Next
            
            '步骤4：仍未找到，记录调试信息并返回Nothing
            Log($"未发现版本 {Id} 的 json 下载地址，版本列表返回为：{vbCrLf}{DlClientListLoader.Output.Value.ToString}", LogLevel.Debug)
            Return Nothing
        Catch ex As Exception
            Log(ex, $"获取版本 {Id} 的 json 下载地址失败")
            Return Nothing
        End Try
    End Function

#End Region

#Region "DlOptiFineList | OptiFine 版本列表"

    ''' <summary>
    ''' OptiFine版本列表结果结构体。
    ''' 用于存储从不同下载源获取到的OptiFine版本列表数据，包含数据来源信息和版本条目列表。
    ''' </summary>
    Public Structure DlOptiFineListResult
        ''' <summary>
        ''' 数据来源名称，如"Official"，"BMCLAPI"。
        ''' 用于标识当前OptiFine版本列表数据来自哪个下载源。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' True表示数据来自OptiFine官方源，False表示来自第三方镜像源如BMCLAPI。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 获取到的数据。
        ''' 包含OptiFine版本条目的列表，每个条目包含详细的版本信息和下载地址。
        ''' </summary>
        Public Value As List(Of DlOptiFineListEntry)
    End Structure

    ''' <summary>
    ''' OptiFine版本条目类。
    ''' 表示一个OptiFine版本的详细信息，包括显示名称、文件名称、对应游戏版本、Forge兼容性等。
    ''' </summary>
    Public Class DlOptiFineListEntry
        ''' <summary>
        ''' 显示名称，已去除 HD_U 字样，如“1.12.2 C8”。
        ''' 用于在用户界面中显示的简洁版本名称，移除了不必要的后缀使显示更清晰。
        ''' </summary>
        Public NameDisplay As String
        ''' <summary>
        ''' 原始文件名称，如“preview_OptiFine_1.11_HD_U_E1_pre.jar”。
        ''' 完整的OptiFine JAR文件名称，包含所有版本标识信息。
        ''' </summary>
        Public NameFile As String
        ''' <summary>
        ''' 对应的版本名称，如“1.13.2-OptiFine_HD_U_E6”。
        ''' 用于Minecraft启动器识别的完整版本标识符，包含Minecraft版本和OptiFine版本信息。
        ''' </summary>
        Public NameVersion As String
        ''' <summary>
        ''' 是否为测试版。
        ''' True表示这是预览版或测试版，可能包含未完全测试的功能；False表示稳定版。
        ''' </summary>
        Public IsPreview As Boolean
        ''' <summary>
        ''' 对应的 Minecraft 版本，如“1.12.2”。
        ''' 此OptiFine版本所基于的Minecraft游戏版本，自动处理版本号格式标准化（移除末尾的.0）。
        ''' </summary>
        Public Property Inherit As String
            Get
                Return _inherit
            End Get
            Set(value As String)
                '标准化版本号格式：移除末尾的.0（如1.8.0 -> 1.8）
                If value.EndsWithF(".0") Then value = Left(value, value.Length - 2)
                _inherit = value
            End Set
        End Property
        Private _inherit As String
        ''' <summary>
        ''' 发布时间，格式为“yyyy/mm/dd”。OptiFine 源无此数据。
        ''' 该OptiFine版本的发布日期，用于显示版本新旧程度。
        ''' </summary>
        Public ReleaseTime As String
        ''' <summary>
        ''' 需要的最低 Forge 版本。空字符串为无限制，Nothing 为不兼容，“28.1.56” 表示版本号，“1161” 表示版本号的最后一位。
        ''' 指定与此OptiFine版本兼容的最低Forge版本要求，用于版本兼容性检查。
        ''' </summary>
        Public RequiredForgeVersion As String
    End Class

    ''' <summary>
    ''' OptiFine版本列表主加载器。
    ''' 作为OptiFine版本列表获取的统一入口，根据用户设置选择不同的下载源策略，管理官方源和镜像源的加载顺序。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，包含输入参数和状态管理</param>
    ''' <remarks>
    ''' 下载源策略说明：
    ''' - Case 0: 优先使用BMCLAPI镜像源（30秒超时），失败后尝试OptiFine官方源（90秒超时）
    ''' - Case 1: 优先使用OptiFine官方源（5秒超时），失败后尝试BMCLAPI镜像源（35秒超时）  
    ''' - Case Else: 仅使用OptiFine官方源（60秒超时），失败后尝试BMCLAPI镜像源（120秒超时）
    ''' </remarks>
    Public DlOptiFineListLoader As New LoaderTask(Of Integer, DlOptiFineListResult)("DlOptiFineList Main", AddressOf DlOptiFineListMain)
    Private Sub DlOptiFineListMain(Loader As LoaderTask(Of Integer, DlOptiFineListResult))
        '根据用户设置选择下载源策略
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                '策略0：优先使用镜像源，降低官方源压力
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListBmclapiLoader, 30),      'BMCLAPI镜像源，30秒超时
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListOfficialLoader, 30 + 60) 'OptiFine官方源，90秒超时（30+60）
                }, Loader.IsForceRestarting)
            Case 1
                '策略1：优先使用官方源，获取最新数据
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListOfficialLoader, 5),        'OptiFine官方源，5秒超时
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListBmclapiLoader, 5 + 30)    'BMCLAPI镜像源，35秒超时（5+30）
                }, Loader.IsForceRestarting)
            Case Else
                '策略2：仅使用官方源，确保数据准确性
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListOfficialLoader, 60),       'OptiFine官方源，60秒超时
                    New KeyValuePair(Of LoaderTask(Of Integer, DlOptiFineListResult), Integer)(DlOptiFineListBmclapiLoader, 60 + 60)   'BMCLAPI镜像源，120秒超时（60+60）
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' OptiFine 版本列表，官方源。
    ''' 从 OptiFine 官方网站获取版本列表，提供最新的官方数据。
    ''' </summary>
    ''' <remarks>
    ''' 主要功能：
    ''' 1. 从 https://optifine.net/downloads 获取 HTML 页面内容
    ''' 2. 使用正则表达式提取版本信息（Forge 兼容性、发布时间、版本名称）
    ''' 3. 验证数据完整性和有效性
    ''' 4. 将 HTML 数据转换为标准化的 DlOptiFineListEntry 对象列表
    ''' 5. 设置官方源标识和来源名称
    ''' 
    ''' 数据验证：
    ''' - 响应内容长度必须大于 200 字符
    ''' - 版本名称、发布时间、Forge 兼容性数据数量必须一致
    ''' - 版本数量必须不少于 10 个
    ''' 
    ''' 异常处理：
    ''' - 网络请求失败会抛出异常
    ''' - 数据解析失败会包装原始异常并重新抛出
    ''' </remarks>
    Public DlOptiFineListOfficialLoader As New LoaderTask(Of Integer, DlOptiFineListResult)("DlOptiFineList Official", AddressOf DlOptiFineListOfficialMain)
    ''' <summary>
    ''' 从 OptiFine 官方网站获取版本列表的主函数。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，用于报告进度和设置结果</param>
    ''' <remarks>
    ''' 处理流程：
    ''' 步骤1：发送 HTTP 请求获取 OptiFine 下载页面
    ''' - 使用 NetRequestByClientRetry 进行重试机制
    ''' - 目标 URL：https://optifine.net/downloads
    ''' - 使用默认编码
    ''' 
    ''' 步骤2：验证响应内容有效性
    ''' - 检查响应长度是否大于 200 字符
    ''' - 长度不足表示可能获取到了错误页面或网络异常
    ''' 
    ''' 步骤3：使用正则表达式提取关键数据
    ''' - Forge 兼容性信息：匹配 colForge'&gt; 后的内容
    ''' - 发布时间信息：匹配 colDate'&gt; 后的内容  
    ''' - 版本名称信息：匹配 OptiFine_ 前缀和 .jar" 后缀之间的内容
    ''' 
    ''' 步骤4：数据完整性验证
    ''' - 确保三个数据列表的数量一致
    ''' - 确保版本数量不少于 10 个（防止获取到不完整数据）
    ''' 
    ''' 步骤5：转换为标准化版本条目
    ''' - 将下划线替换为空格以提高可读性
    ''' - 设置显示名称（移除 HD U 前缀和 .0 后缀）
    ''' - 格式化发布时间为 YYYY/MM/DD 格式
    ''' - 检测预览版（包含 "pre" 字样）
    ''' - 提取 Minecraft 版本号（版本名称的第一个部分）
    ''' - 生成文件名（预览版添加 preview_ 前缀）
    ''' - 处理 Forge 版本号（移除 Forge 前缀和 # 符号）
    ''' - 生成版本标识符（Minecraft版本-OptiFine_版本名称格式）
    ''' 
    ''' 步骤6：设置加载器输出结果
    ''' - 标记为官方数据源（IsOfficial = True）
    ''' - 设置来源名称为 "OptiFine 官方源"
    ''' - 将转换后的版本列表赋值给 Value 属性
    ''' </remarks>
    Private Sub DlOptiFineListOfficialMain(Loader As LoaderTask(Of Integer, DlOptiFineListResult))
        Dim Result As String = NetRequestByClientRetry("https://optifine.net/downloads", Encoding:=Encoding.Default)
        If Result.Length < 200 Then Throw New Exception("获取到的版本列表长度不足（" & Result & "）")
        Try
            '获取所有版本信息
            Dim Forge As List(Of String) = RegexSearch(Result, "(?<=colForge'>)[^<]*")
            Dim ReleaseTime As List(Of String) = RegexSearch(Result, "(?<=colDate'>)[^<]+")
            Dim Name As List(Of String) = RegexSearch(Result, "(?<=OptiFine_)[0-9A-Za-z_.]+(?=.jar"")")
            If Not ReleaseTime.Count = Name.Count Then Throw New Exception("版本与发布时间数据无法对应")
            If Not Forge.Count = Name.Count Then Throw New Exception("版本与 Forge 兼容数据无法对应")
            If ReleaseTime.Count < 10 Then Throw New Exception("获取到的版本数量不足（" & Result & "）")
            '转化为列表输出
            Dim Versions As New List(Of DlOptiFineListEntry)
            For i = 0 To ReleaseTime.Count - 1
                Name(i) = Name(i).Replace("_", " ")
                Dim Entry As New DlOptiFineListEntry With {
                             .NameDisplay = Name(i).Replace("HD U ", "").Replace(".0 ", " "),
                             .ReleaseTime = Join({ReleaseTime(i).Split(".")(2), ReleaseTime(i).Split(".")(1), ReleaseTime(i).Split(".")(0)}, "/"),
                             .IsPreview = Name(i).ContainsF("pre", True),
                             .Inherit = Name(i).ToString.Split(" ")(0),
                             .NameFile = If(Name(i).ContainsF("pre", True), "preview_", "") & "OptiFine_" & Name(i).Replace(" ", "_") & ".jar",
                             .RequiredForgeVersion = Forge(i).Replace("Forge ", "").Replace("#", "")}
                If Entry.RequiredForgeVersion.Contains("N/A") Then Entry.RequiredForgeVersion = Nothing
                Entry.NameVersion = Entry.Inherit & "-OptiFine_" & Name(i).ToString.Replace(" ", "_").Replace(Entry.Inherit & "_", "")
                Versions.Add(Entry)
            Next
            Loader.Output = New DlOptiFineListResult With {.IsOfficial = True, .SourceName = "OptiFine 官方源", .Value = Versions}
        Catch ex As Exception
            Throw New Exception("OptiFine 官方源版本列表解析失败（" & Result & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' OptiFine 版本列表，BMCLAPI。
    ''' </summary>
    Public DlOptiFineListBmclapiLoader As New LoaderTask(Of Integer, DlOptiFineListResult)("DlOptiFineList Bmclapi", AddressOf DlOptiFineListBmclapiMain)
    Private Sub DlOptiFineListBmclapiMain(Loader As LoaderTask(Of Integer, DlOptiFineListResult))
        Dim Json As JArray = GetJson(NetRequestByClientRetry("https://bmclapi2.bangbang93.com/optifine/versionList", RequireJson:=True))
        Try
            Dim Versions As New List(Of DlOptiFineListEntry)
            For Each Token As JObject In Json
                Dim Entry As New DlOptiFineListEntry With {
                             .NameDisplay = (Token("mcversion").ToString & Token("type").ToString.Replace("HD_U", "").Replace("_", " ") & " " & Token("patch").ToString).Replace(".0 ", " "),
                             .ReleaseTime = "",
                             .IsPreview = Token("patch").ToString.ContainsF("pre", True),
                             .Inherit = Token("mcversion").ToString,
                             .NameFile = Token("filename").ToString,
                             .RequiredForgeVersion = If(Token("forge"), "").ToString.Replace("Forge ", "").Replace("#", "")
                         }
                If Entry.RequiredForgeVersion.Contains("N/A") Then Entry.RequiredForgeVersion = Nothing
                Entry.NameVersion = Entry.Inherit & "-OptiFine_" & (Token("type").ToString & " " & Token("patch").ToString).Replace(".0 ", " ").Replace(" ", "_").Replace(Entry.Inherit & "_", "")
                Versions.Add(Entry)
            Next
            Loader.Output = New DlOptiFineListResult With {.IsOfficial = False, .SourceName = "BMCLAPI", .Value = Versions}
        Catch ex As Exception
            Throw New Exception("OptiFine BMCLAPI 版本列表解析失败（" & Json.ToString & "）", ex)
        End Try
    End Sub

#End Region

#Region "DlForgeList | Forge Minecraft 版本列表"

    Public Structure DlForgeListResult
        ''' <summary>
        ''' 数据来源名称，如“Official”，“BMCLAPI”。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 获取到的数据。
        ''' </summary>
        Public Value As List(Of String)
    End Structure

    ''' <summary>
    ''' Forge 版本列表，主加载器。
    ''' </summary>
    Public DlForgeListLoader As New LoaderTask(Of Integer, DlForgeListResult)("DlForgeList Main", AddressOf DlForgeListMain)
    Private Sub DlForgeListMain(Loader As LoaderTask(Of Integer, DlForgeListResult))
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListBmclapiLoader, 30),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListOfficialLoader, 30 + 60)
                }, Loader.IsForceRestarting)
            Case 1
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListOfficialLoader, 5),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListBmclapiLoader, 5 + 30)
                }, Loader.IsForceRestarting)
            Case Else
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListOfficialLoader, 60),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlForgeListResult), Integer)(DlForgeListBmclapiLoader, 60 + 60)
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' Forge 版本列表，官方源。
    ''' </summary>
    Public DlForgeListOfficialLoader As New LoaderTask(Of Integer, DlForgeListResult)("DlForgeList Official", AddressOf DlForgeListOfficialMain)
    Private Sub DlForgeListOfficialMain(Loader As LoaderTask(Of Integer, DlForgeListResult))
        Dim Result As String = NetRequestByClientRetry("https://files.minecraftforge.net/maven/net/minecraftforge/forge/index_1.2.4.html", Encoding:=Encoding.Default, Accept:="text/html", SimulateBrowserHeaders:=True)
        If Result.Length < 200 Then Throw New Exception("获取到的版本列表长度不足（" & Result & "）")
        '获取所有版本信息
        Dim Names As List(Of String) = RegexSearch(Result, "(?<=a href=""index_)[0-9.]+(_pre[0-9]?)?(?=.html)")
        Names.Add("1.2.4") '1.2.4 不会被匹配上
        If Names.Count < 10 Then Throw New Exception("获取到的版本数量不足（" & Result & "）")
        Loader.Output = New DlForgeListResult With {.IsOfficial = True, .SourceName = "Forge 官方源", .Value = Names}
    End Sub

    ''' <summary>
    ''' Forge 版本列表，BMCLAPI。
    ''' </summary>
    Public DlForgeListBmclapiLoader As New LoaderTask(Of Integer, DlForgeListResult)("DlForgeList Bmclapi", AddressOf DlForgeListBmclapiMain)
    Private Sub DlForgeListBmclapiMain(Loader As LoaderTask(Of Integer, DlForgeListResult))
        Dim Result As String = NetRequestByClientRetry("https://bmclapi2.bangbang93.com/forge/minecraft", Encoding:=Encoding.Default)
        If Result.Length < 200 Then Throw New Exception("获取到的版本列表长度不足（" & Result & "）")
        '获取所有版本信息
        Dim Names As List(Of String) = RegexSearch(Result, "[0-9.]+(_pre[0-9]?)?")
        If Names.Count < 10 Then Throw New Exception("获取到的版本数量不足（" & Result & "）")
        Loader.Output = New DlForgeListResult With {.IsOfficial = False, .SourceName = "BMCLAPI", .Value = Names}
    End Sub

#End Region

#Region "DlForgeVersion | Forge 版本列表"

    Public MustInherit Class DlForgelikeEntry
        Public IsNeoForge As Boolean
        ''' <summary>
        ''' 加载器名称。Forge 或 NeoForge。
        ''' </summary>
        Public ReadOnly Property LoaderName As String
            Get
                Return If(IsNeoForge, "NeoForge", "Forge")
            End Get
        End Property
        ''' <summary>
        ''' 文件扩展名。不以小数点开头。
        ''' </summary>
        Public ReadOnly Property FileExtension As String
            Get
                If IsNeoForge Then
                    Return "jar"
                Else
                    Return If(CType(Me, DlForgeVersionEntry).Category = "installer", "jar", "zip")
                End If
            End Get
        End Property
        ''' <summary>
        ''' Forge：MC 版本是否小于 1.13。
        ''' NeoForge：MC 版本是否为 1.20.1。
        ''' </summary>
        Public ReadOnly Property IsLegacy As Boolean
            Get
                '虽然很抽象，但确实可以这样判断
                'Forge：1.13+ 的版本号首位都大于 20
                'NeoForge：1.20.1 的版本号首位人为规定为 19 开头
                Return Version.Major < 20
            End Get
        End Property
        ''' <summary>
        ''' 标准化后的版本号，仅可用于比较与排序。
        ''' 格式：Major.Minor.Build.Revision
        ''' Forge：如 “50.1.9.0”（最后一位固定为 0）、“14.22.1.2478”（Legacy）。
        ''' NeoForge：如 “20.4.30.0”（最后一位固定为 0）、“19.47.1.99”（Legacy：第一位固定为 19）。
        ''' </summary>
        Public Version As Version
        ''' <summary>
        ''' 可对玩家显示的非格式化版本名。
        ''' Forge：如 “50.1.9”、“14.22.1.2478”（Legacy）。
        ''' NeoForge：如 “20.4.30-beta”、“47.1.99”（Legacy）。
        ''' </summary>
        Public VersionName As String
        ''' <summary>
        ''' 对应的 Minecraft 版本，如“1.12.2”。
        ''' </summary>
        Public Inherit As String
    End Class

    Public Class DlForgeVersionEntry
        Inherits DlForgelikeEntry
        ''' <summary>
        ''' 发布时间，格式为“yyyy/MM/dd HH:mm”。
        ''' </summary>
        Public ReleaseTime As String
        ''' <summary>
        ''' 文件的 MD5 或 SHA1（BMCLAPI 的老版本是 MD5，新版本是 SHA1；官方源总是 MD5）。
        ''' </summary>
        Public Hash As String = Nothing
        ''' <summary>
        ''' 是否为推荐版本。
        ''' </summary>
        Public IsRecommended As Boolean
        ''' <summary>
        ''' 安装类型。有 installer、client、universal 三种。
        ''' </summary>
        Public Category As String
        ''' <summary>
        ''' 用于下载的文件版本名。可能在 Version 的基础上添加了分支。
        ''' </summary>
        Public FileVersion As String

        Public Sub New(Version As String, Branch As String, Inherit As String)
            '司马版本的特殊处理
            If Version = "11.15.1.2318" OrElse Version = "11.15.1.1902" OrElse Version = "11.15.1.1890" Then Branch = "1.8.9"
            If Branch Is Nothing AndAlso Inherit = "1.7.10" AndAlso Version.Split(".")(3) >= 1300 Then Branch = "1.7.10"
            '为 DlForgelikeEntry 提供所有信息
            IsNeoForge = False
            VersionName = Version
            Me.Version = New Version(Version)
            Me.Inherit = Inherit
            FileVersion = Version & If(Branch Is Nothing, "", "-" & Branch)
        End Sub
    End Class

    ''' <summary>
    ''' Forge 版本列表，主加载器。
    ''' </summary>
    Public Sub DlForgeVersionMain(Loader As LoaderTask(Of String, List(Of DlForgeVersionEntry)))
        Dim DlForgeVersionOfficialLoader As New LoaderTask(Of String, List(Of DlForgeVersionEntry))("DlForgeVersion Official", AddressOf DlForgeVersionOfficialMain)
        Dim DlForgeVersionBmclapiLoader As New LoaderTask(Of String, List(Of DlForgeVersionEntry))("DlForgeVersion Bmclapi", AddressOf DlForgeVersionBmclapiMain)
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionBmclapiLoader, 30),
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionOfficialLoader, 30 + 60)
                }, Loader.IsForceRestarting)
            Case 1
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionOfficialLoader, 5),
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionBmclapiLoader, 5 + 30)
                }, Loader.IsForceRestarting)
            Case Else
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionOfficialLoader, 60),
                    New KeyValuePair(Of LoaderTask(Of String, List(Of DlForgeVersionEntry)), Integer)(DlForgeVersionBmclapiLoader, 60 + 60)
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' Forge 版本列表，官方源。
    ''' </summary>
    Public Sub DlForgeVersionOfficialMain(Loader As LoaderTask(Of String, List(Of DlForgeVersionEntry)))
        Dim Result As String
        Try
            Result = NetRequestByLoader("https://files.minecraftforge.net/maven/net/minecraftforge/forge/index_" &
                                          Loader.Input.Replace("-", "_") & '兼容 Forge 1.7.10-pre4，#4057
                                          ".html", SimulateBrowserHeaders:=True)
        Catch ex As Exception
            If ex.GetBrief().Contains("(404)") Then
                Throw New Exception("不可用")
            Else
                Throw
            End If
        End Try
        If Result.Length < 1000 Then Throw New Exception("获取到的版本列表长度不足（" & Result & "）")
        Dim Versions As New List(Of DlForgeVersionEntry)
        Try
            '分割版本信息
            Dim VersionCodes = Mid(Result, 1, Result.LastIndexOfF("</table>")).Split("<td class=""download-version")
            '获取所有版本信息
            For i = 1 To VersionCodes.Count - 1
                Dim VersionCode = VersionCodes(i)
                Try
                    '基础信息获取
                    Dim Name As String = RegexSeek(VersionCode, "(?<=[^(0-9)]+)[0-9\.]+")
                    Dim IsRecommended As Boolean = VersionCode.Contains("fa promo-recommended")
                    Dim Inherit As String = Loader.Input
                    '分支获取
                    Dim Branch As String = RegexSeek(VersionCode, $"(?<=-{Name}-)[^-""]+(?=-[a-z]+.[a-z]{{3}})")
                    If String.IsNullOrWhiteSpace(Branch) Then Branch = Nothing
                    '发布时间获取
                    Dim ReleaseTimeOriginal = RegexSeek(VersionCode, "(?<=""download-time"" title="")[^""]+")
                    Dim ReleaseTimeSplit = ReleaseTimeOriginal.Split(" -:".ToCharArray) '原格式："2021-02-15 03:24:02"
                    Dim ReleaseDate As New Date(ReleaseTimeSplit(0), ReleaseTimeSplit(1), ReleaseTimeSplit(2), '年月日
                                                ReleaseTimeSplit(3), ReleaseTimeSplit(4), ReleaseTimeSplit(5), '时分秒
                                                0, DateTimeKind.Utc) '以 UTC 时间作为标准
                    Dim ReleaseTime As String = ReleaseDate.ToLocalTime.ToString("yyyy'/'MM'/'dd HH':'mm") '时区与格式转换
                    '分类与 MD5 获取
                    Dim MD5 As String, Category As String
                    If VersionCode.Contains("classifier-installer""") Then
                        '类型为 installer.jar，支持范围 ~753 (~ 1.6.1 部分), 738~684 (1.5.2 全部)
                        VersionCode = VersionCode.Substring(VersionCode.IndexOfF("installer.jar"))
                        MD5 = RegexSeek(VersionCode, "(?<=MD5:</strong> )[^<]+")
                        Category = "installer"
                    ElseIf VersionCode.Contains("classifier-universal""") Then
                        '类型为 universal.zip，支持范围 751~449 (1.6.1 部分), 682~183 (1.5.1 ~ 1.3.2 部分)
                        VersionCode = VersionCode.Substring(VersionCode.IndexOfF("universal.zip"))
                        MD5 = RegexSeek(VersionCode, "(?<=MD5:</strong> )[^<]+")
                        Category = "universal"
                    ElseIf VersionCode.Contains("client.zip") Then
                        '类型为 client.zip，支持范围 182~ (1.3.2 部分 ~)
                        VersionCode = VersionCode.Substring(VersionCode.IndexOfF("client.zip"))
                        MD5 = RegexSeek(VersionCode, "(?<=MD5:</strong> )[^<]+")
                        Category = "client"
                    Else
                        '没有任何下载（1.6.4 有一部分这种情况）
                        Continue For
                    End If
                    '添加进列表
                    Versions.Add(New DlForgeVersionEntry(Name, Branch, Inherit) With {.Category = Category, .IsRecommended = IsRecommended, .Hash = MD5.Trim(vbCr, vbLf), .ReleaseTime = ReleaseTime})
                Catch ex As Exception
                    Throw New Exception("Forge 官方源版本信息提取失败（" & VersionCode & "）", ex)
                End Try
            Next
        Catch ex As Exception
            Throw New Exception("Forge 官方源版本列表解析失败（" & Result & "）", ex)
        End Try
        If Not Versions.Any() Then Throw New Exception("不可用")
        Loader.Output = Versions
    End Sub

    ''' <summary>
    ''' Forge 版本列表，BMCLAPI。
    ''' </summary>
    Public Sub DlForgeVersionBmclapiMain(Loader As LoaderTask(Of String, List(Of DlForgeVersionEntry)))
        Dim Json As JArray = GetJson(NetRequestByClientRetry("https://bmclapi2.bangbang93.com/forge/minecraft/" &
                                                      Loader.Input.Replace("-", "_"), RequireJson:=True)) '兼容 Forge 1.7.10-pre4，#4057
        Dim Versions As New List(Of DlForgeVersionEntry)
        Try
            Dim Recommended As String = McDownloadForgeRecommendedGet(Loader.Input)
            For Each Token As JObject In Json
                '分类与 Hash 获取
                Dim Hash As String = Nothing, Category As String = "unknown", Proi As Integer = -1
                For Each File As JObject In Token("files")
                    Select Case File("category").ToString
                        Case "installer"
                            If File("format").ToString = "jar" Then
                                '类型为 installer.jar，支持范围 ~753 (~ 1.6.1 部分), 738~684 (1.5.2 全部)
                                Hash = File("hash")
                                Category = "installer"
                                Proi = 2
                            End If
                        Case "universal"
                            If Proi <= 1 AndAlso File("format").ToString = "zip" Then
                                '类型为 universal.zip，支持范围 751~449 (1.6.1 部分), 682~183 (1.5.1 ~ 1.3.2 部分)
                                Hash = File("hash")
                                Category = "universal"
                                Proi = 1
                            End If
                        Case "client"
                            If Proi <= 0 AndAlso File("format").ToString = "zip" Then
                                '类型为 client.zip，支持范围 182~ (1.3.2 部分 ~)
                                Hash = File("hash")
                                Category = "client"
                                Proi = 0
                            End If
                    End Select
                Next
                '获取 Entry
                Dim Branch As String = Token("branch")
                Dim Name As String = Token("version")
                '基础信息获取
                Dim Entry = New DlForgeVersionEntry(Name, Branch, Loader.Input) With {.Hash = Hash, .Category = Category, .IsRecommended = Recommended = Name}
                Dim TimeSplit = Token("modified").ToString.Split("-"c, "T"c, ":"c, "."c, " "c, "/"c)
                Entry.ReleaseTime = Token("modified").ToObject(Of Date).ToLocalTime.ToString("yyyy'/'MM'/'dd HH':'mm")
                '添加项
                Versions.Add(Entry)
            Next
        Catch ex As Exception
            Throw New Exception("Forge BMCLAPI 版本列表解析失败（" & Json.ToString & "）", ex)
        End Try
        If Not Versions.Any() Then Throw New Exception("不可用")
        Loader.Output = Versions
    End Sub

#End Region

#Region "DlNeoForgeList | NeoForge 版本列表"

    Public Structure DlNeoForgeListResult
        ''' <summary>
        ''' 数据来源名称，如“Official”，“BMCLAPI”。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 所有版本的列表。已经按从新到老排序。
        ''' </summary>
        Public Value As List(Of DlNeoForgeListEntry)
    End Structure

    Public Class DlNeoForgeListEntry
        Inherits DlForgelikeEntry
        ''' <summary>
        ''' 是否是 Beta 版。
        ''' </summary>
        Public IsBeta As Boolean
        ''' <summary>
        ''' API 使用的原始版本字符串，如 “20.4.30-beta”、“1.20.1-47.1.99”（Legacy）。
        ''' </summary>
        Public ApiName As String
        ''' <summary>
        ''' 文件在官网的基础地址，不包含后缀。
        ''' </summary>
        Public ReadOnly Property UrlBase As String
            Get
                Dim PackageName As String = If(IsLegacy, "forge", "neoforge")
                Return $"https://maven.neoforged.net/releases/net/neoforged/{PackageName}/{ApiName}/{PackageName}-{ApiName}"
            End Get
        End Property

        Public Sub New(ApiName As String)
            IsNeoForge = True
            Me.ApiName = ApiName
            IsBeta = ApiName.Contains("beta")
            If ApiName.Contains("1.20.1") Then '1.20.1-47.1.99
                VersionName = ApiName.Replace("1.20.1-", "")
                Version = New Version("19." & VersionName)
                Inherit = "1.20.1"
            Else '20.4.30-beta
                VersionName = ApiName
                Version = New Version(ApiName.BeforeFirst("-"))
                Inherit = $"1.{Version.Major}" & If(Version.Minor = 0, "", "." & Version.Minor)
            End If
        End Sub
    End Class

    ''' <summary>
    ''' NeoForge 版本列表，主加载器。
    ''' </summary>
    Public DlNeoForgeListLoader As New LoaderTask(Of Integer, DlNeoForgeListResult)("DlNeoForgeList Main", AddressOf DlNeoForgeListMain)
    Private Sub DlNeoForgeListMain(Loader As LoaderTask(Of Integer, DlNeoForgeListResult))
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListBmclapiLoader, 30),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListOfficialLoader, 30 + 60)
                }, Loader.IsForceRestarting)
            Case 1
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListOfficialLoader, 5),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListBmclapiLoader, 5 + 30)
                }, Loader.IsForceRestarting)
            Case Else
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListOfficialLoader, 60),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlNeoForgeListResult), Integer)(DlNeoForgeListBmclapiLoader, 60 + 60)
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' NeoForge 版本列表，官方源。
    ''' </summary>
    Public DlNeoForgeListOfficialLoader As New LoaderTask(Of Integer, DlNeoForgeListResult)("DlNeoForgeList Official", AddressOf DlNeoForgeListOfficialMain)
    Private Sub DlNeoForgeListOfficialMain(Loader As LoaderTask(Of Integer, DlNeoForgeListResult))
        '获取版本列表 JSON
        Dim ResultLatest As String = NetRequestByClientRetry("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge", RequireJson:=True)
        Dim ResultLegacy As String = NetRequestByClientRetry("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/forge", RequireJson:=True)
        If ResultLatest.Length < 100 OrElse ResultLegacy.Length < 100 Then Throw New Exception("获取到的版本列表长度不足（" & ResultLatest & "）")
        '解析
        Try
            Loader.Output = New DlNeoForgeListResult With {.IsOfficial = True, .SourceName = "NeoForge 官方源",
                .Value = GetNeoForgeEntries(ResultLatest, ResultLegacy)}
        Catch ex As Exception
            Throw New Exception("NeoForge 官方源版本列表解析失败（" & ResultLatest & vbCrLf & vbCrLf & ResultLegacy & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' NeoForge 版本列表，BMCLAPI。
    ''' </summary>
    Public DlNeoForgeListBmclapiLoader As New LoaderTask(Of Integer, DlNeoForgeListResult)("DlNeoForgeList Bmclapi", AddressOf DlNeoForgeListBmclapiMain)
    Public Sub DlNeoForgeListBmclapiMain(Loader As LoaderTask(Of Integer, DlNeoForgeListResult))
        '获取版本列表 JSON
        Dim ResultLatest As String = NetRequestByClientRetry("https://bmclapi2.bangbang93.com/neoforge/meta/api/maven/details/releases/net/neoforged/neoforge", RequireJson:=True)
        Dim ResultLegacy As String = NetRequestByClientRetry("https://bmclapi2.bangbang93.com/neoforge/meta/api/maven/details/releases/net/neoforged/forge", RequireJson:=True)
        If ResultLatest.Length < 100 OrElse ResultLegacy.Length < 100 Then Throw New Exception("获取到的版本列表长度不足（" & ResultLatest & "）")
        '解析
        Try
            Loader.Output = New DlNeoForgeListResult With {.IsOfficial = True, .SourceName = "BMCLAPI",
                .Value = GetNeoForgeEntries(ResultLatest, ResultLegacy)}
        Catch ex As Exception
            Throw New Exception("NeoForge BMCLAPI 版本列表解析失败（" & ResultLatest & vbCrLf & vbCrLf & ResultLegacy & "）", ex)
        End Try
    End Sub

    Private Function GetNeoForgeEntries(LatestJson As String, LatestLegacyJson As String) As List(Of DlNeoForgeListEntry)
        Dim VersionNames = RegexSearch(LatestLegacyJson & LatestJson,
            "(?<="")(1\.20\.1-)?\d+\.\d+\.\d+(-beta)?(?="")") '我寻思直接正则就行.jpg
        Dim Versions = VersionNames.
            Where(Function(name) name <> "47.1.82"). '这个版本虽然在版本列表中，但不能下载
            Select(Function(name) New DlNeoForgeListEntry(name)).ToList
        If Not Versions.Any() Then Throw New Exception("不可用")
        Versions = Versions.OrderByDescending(Function(a) a.Version).ToList
        Return Versions
    End Function

#End Region

#Region "DlLiteLoaderList | LiteLoader 版本列表"

    Public Structure DlLiteLoaderListResult
        ''' <summary>
        ''' 数据来源名称，如“Official”，“BMCLAPI”。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 获取到的数据。
        ''' </summary>
        Public Value As List(Of DlLiteLoaderListEntry)
        ''' <summary>
        ''' 官方源的失败原因。若没有则为 Nothing。
        ''' </summary>
        Public OfficialError As Exception
    End Structure

    Public Class DlLiteLoaderListEntry
        ''' <summary>
        ''' 实际的文件名，如“liteloader-installer-1.12-00-SNAPSHOT.jar”。
        ''' </summary>
        Public FileName As String
        ''' <summary>
        ''' 是否为测试版。
        ''' </summary>
        Public IsPreview As Boolean
        ''' <summary>
        ''' 对应的 Minecraft 版本，如“1.12.2”。
        ''' </summary>
        Public Inherit As String
        ''' <summary>
        ''' 是否为 1.7 及更早的远古版。
        ''' </summary>
        Public IsLegacy As Boolean
        ''' <summary>
        ''' 发布时间，格式为“yyyy/mm/dd HH:mm”。
        ''' </summary>
        Public ReleaseTime As String
        ''' <summary>
        ''' 文件的 MD5。
        ''' </summary>
        Public MD5 As String
        ''' <summary>
        ''' 对应的 Json 项。
        ''' </summary>
        Public JsonToken As JToken
    End Class

    ''' <summary>
    ''' LiteLoader 版本列表，主加载器。
    ''' </summary>
    Public DlLiteLoaderListLoader As New LoaderTask(Of Integer, DlLiteLoaderListResult)("DlLiteLoaderList Main", AddressOf DlLiteLoaderListMain)
    Private Sub DlLiteLoaderListMain(Loader As LoaderTask(Of Integer, DlLiteLoaderListResult))
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListBmclapiLoader, 30),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListOfficialLoader, 30 + 60)
                }, Loader.IsForceRestarting)
            Case 1
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListOfficialLoader, 5),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListBmclapiLoader, 5 + 30)
                }, Loader.IsForceRestarting)
            Case Else
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListOfficialLoader, 60),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlLiteLoaderListResult), Integer)(DlLiteLoaderListBmclapiLoader, 60 + 60)
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' LiteLoader 版本列表，官方源。
    ''' </summary>
    Public DlLiteLoaderListOfficialLoader As New LoaderTask(Of Integer, DlLiteLoaderListResult)("DlLiteLoaderList Official", AddressOf DlLiteLoaderListOfficialMain)
    Private Sub DlLiteLoaderListOfficialMain(Loader As LoaderTask(Of Integer, DlLiteLoaderListResult))
        Dim Result As JObject = GetJson(NetRequestByClientRetry("https://dl.liteloader.com/versions/versions.json", RequireJson:=True))
        Try
            Dim Json As JObject = Result("versions")
            Dim Versions As New List(Of DlLiteLoaderListEntry)
            For Each Pair As KeyValuePair(Of String, JToken) In Json
                If Pair.Key.StartsWithF("1.6") OrElse Pair.Key.StartsWithF("1.5") Then Continue For
                Dim RealEntry As JToken = If(Pair.Value("artefacts"), Pair.Value("snapshots"))("com.mumfrey:liteloader")("latest")
                Versions.Add(New DlLiteLoaderListEntry With {
                             .Inherit = Pair.Key,
                             .IsLegacy = Pair.Key.Split(".")(1) < 8,
                             .IsPreview = RealEntry("stream").ToString.ToLower = "snapshot",
                             .FileName = "liteloader-installer-" & Pair.Key & If(Pair.Key = "1.8" OrElse Pair.Key = "1.9", ".0", "") & "-00-SNAPSHOT.jar",
                             .MD5 = RealEntry("md5"),
                             .ReleaseTime = GetLocalTime(GetDate(RealEntry("timestamp"))).ToString("yyyy'/'MM'/'dd HH':'mm"),
                             .JsonToken = RealEntry
                         })
            Next
            Loader.Output = New DlLiteLoaderListResult With {.IsOfficial = True, .SourceName = "LiteLoader 官方源", .Value = Versions}
        Catch ex As Exception
            Throw New Exception("LiteLoader 官方源版本列表解析失败（" & Result.ToString & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' LiteLoader 版本列表，BMCLAPI。
    ''' 从 BMCLAPI 镜像源获取 LiteLoader 版本列表数据。
    ''' </summary>
    ''' <remarks>
    ''' 主要功能：
    ''' 1. 从 BMCLAPI 获取 LiteLoader 版本 JSON 数据
    ''' 2. 解析 JSON 结构，提取各 Minecraft 版本对应的 LiteLoader 版本信息
    ''' 3. 过滤掉 1.5 和 1.6 版本（过旧版本）
    ''' 4. 为每个版本创建 DlLiteLoaderListEntry 条目
    ''' 5. 设置 BMCLAPI 源标识和来源名称
    ''' 
    ''' 数据结构：
    ''' - 使用 versions.json 获取版本列表
    ''' - 每个 Minecraft 版本对应 artefacts 或 snapshots 中的最新版本
    ''' - 提取文件名、MD5、时间戳等关键信息
    ''' 
    ''' 异常处理：
    ''' - 网络请求失败会抛出异常
    ''' - JSON 解析失败会包装原始异常并重新抛出
    ''' </remarks>
    Public DlLiteLoaderListBmclapiLoader As New LoaderTask(Of Integer, DlLiteLoaderListResult)("DlLiteLoaderList Bmclapi", AddressOf DlLiteLoaderListBmclapiMain)
    ''' <summary>
    ''' 从 BMCLAPI 获取 LiteLoader 版本列表的主函数。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，用于报告进度和设置结果</param>
    ''' <remarks>
    ''' 处理流程：
    ''' 步骤1：发送 HTTP 请求获取 LiteLoader 版本 JSON 数据
    ''' - 使用 NetRequestByClientRetry 进行重试机制
    ''' - 目标 URL：https://bmclapi2.bangbang93.com/maven/com/mumfrey/liteloader/versions.json
    ''' - 要求返回 JSON 格式数据
    ''' 
    ''' 步骤2：解析 JSON 数据结构
    ''' - 提取 versions 对象作为主要的版本数据容器
    ''' - 遍历每个 Minecraft 版本作为键值对
    ''' 
    ''' 步骤3：版本过滤和处理
    ''' - 跳过 1.5 和 1.6 版本（过旧版本，不兼容）
    ''' - 对于每个版本，获取 artefacts 或 snapshots 中的最新版本信息
    ''' - 优先使用 artefacts（正式版本），不存在时使用 snapshots（快照版本）
    ''' 
    ''' 步骤4：创建版本条目
    ''' - 设置 Minecraft 版本号（Inherit）
    ''' - 判断是否为旧版本（1.8 以下版本标记为 IsLegacy）
    ''' - 检测是否为预览版（stream 值为 "snapshot"）
    ''' - 生成安装器文件名（特殊处理 1.8 和 1.9 版本添加 .0）
    ''' - 提取 MD5 校验值
    ''' - 转换时间戳为本地时间格式
    ''' - 保存原始 JSON 数据供后续使用
    ''' 
    ''' 步骤5：设置加载器输出结果
    ''' - 标记为非官方数据源（IsOfficial = False）
    ''' - 设置来源名称为 "BMCLAPI"
    ''' - 将转换后的版本列表赋值给 Value 属性
    ''' </remarks>
    Private Sub DlLiteLoaderListBmclapiMain(Loader As LoaderTask(Of Integer, DlLiteLoaderListResult))
        '发送 HTTP 请求获取 LiteLoader 版本 JSON 数据，要求返回 JSON 格式
        Dim Result As JObject = GetJson(NetRequestByClientRetry("https://bmclapi2.bangbang93.com/maven/com/mumfrey/liteloader/versions.json", RequireJson:=True))
        Try
            '提取 versions 对象作为主要的版本数据容器
            Dim Json As JObject = Result("versions")
            '创建版本列表用于存储转换后的 DlLiteLoaderListEntry 对象
            Dim Versions As New List(Of DlLiteLoaderListEntry)
            
            '遍历每个 Minecraft 版本作为键值对
            For Each Pair As KeyValuePair(Of String, JToken) In Json
                '跳过 1.5 和 1.6 版本（过旧版本，不兼容）
                If Pair.Key.StartsWithF("1.6") OrElse Pair.Key.StartsWithF("1.5") Then Continue For
                
                '获取 artefacts 或 snapshots 中的最新版本信息
                '优先使用 artefacts（正式版本），不存在时使用 snapshots（快照版本）
                Dim RealEntry As JToken = If(Pair.Value("artefacts"), Pair.Value("snapshots"))("com.mumfrey:liteloader")("latest")
                
                '创建新的 DlLiteLoaderListEntry 对象并设置各个属性
                Versions.Add(New DlLiteLoaderListEntry With {
                             '设置 Minecraft 版本号
                             .Inherit = Pair.Key,
                             '判断是否为旧版本（1.8 以下版本）
                             .IsLegacy = Pair.Key.Split(".")(1) < 8,
                             '检测是否为预览版（stream 值为 "snapshot"）
                             .IsPreview = RealEntry("stream").ToString.ToLower = "snapshot",
                             '生成安装器文件名，特殊处理 1.8 和 1.9 版本添加 .0
                             .FileName = "liteloader-installer-" & Pair.Key & If(Pair.Key = "1.8" OrElse Pair.Key = "1.9", ".0", "") & "-00-SNAPSHOT.jar",
                             '提取 MD5 校验值
                             .MD5 = RealEntry("md5"),
                             '转换时间戳为本地时间格式
                             .ReleaseTime = GetLocalTime(GetDate(RealEntry("timestamp"))).ToString("yyyy'/'MM'/'dd HH':'mm"),
                             '保存原始 JSON 数据供后续使用
                             .JsonToken = RealEntry
                         })
            Next
            
            '设置加载器输出结果
            '标记为非官方数据源（IsOfficial = False），设置来源名称，并将转换后的版本列表赋值给 Value 属性
            Loader.Output = New DlLiteLoaderListResult With {.IsOfficial = False, .SourceName = "BMCLAPI", .Value = Versions}
        Catch ex As Exception
            '异常处理：包装原始异常并重新抛出，包含原始响应数据用于调试
            Throw New Exception("LiteLoader BMCLAPI 版本列表解析失败（" & Result.ToString & "）", ex)
        End Try
    End Sub

#End Region

#Region "DlFabricList | Fabric 列表"

    Public Structure DlFabricListResult
        ''' <summary>
        ''' 数据来源名称，如“Official”，“BMCLAPI”。
        ''' </summary>
        Public SourceName As String
        ''' <summary>
        ''' 是否为官方的实时数据。
        ''' </summary>
        Public IsOfficial As Boolean
        ''' <summary>
        ''' 获取到的数据。
        ''' </summary>
        Public Value As JObject
    End Structure

    ''' <summary>
    ''' Fabric 列表，主加载器。
    ''' </summary>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 协调 Fabric 官方源和 BMCLAPI 镜像源的数据获取
    ''' - 根据用户设置选择优先使用的数据源
    ''' - 提供智能失败重试机制，确保数据获取成功率
    ''' 
    ''' 主要功能：
    ''' 1. 策略选择：根据 ToolDownloadVersion 设置选择数据源优先级
    ''' 2. 超时控制：为每个数据源设置合理的超时时间
    ''' 3. 失败重试：使用 DlSourceLoader 实现智能重试机制
    ''' 4. 结果传递：将成功获取的数据传递给调用者
    ''' 
    ''' 数据源策略：
    ''' - Case 0：优先使用 BMCLAPI（30s），失败后使用官方源（90s）
    ''' - Case 1：优先使用官方源（5s），失败后使用 BMCLAPI（35s）
    ''' - Case Else：优先使用官方源（60s），失败后使用 BMCLAPI（120s）
    ''' 
    ''' 异常处理：
    ''' - 所有数据源都失败时抛出异常
    ''' - 保留原始异常信息用于调试
    ''' - 支持强制重启机制
    ''' </remarks>
    Public DlFabricListLoader As New LoaderTask(Of Integer, DlFabricListResult)("DlFabricList Main", AddressOf DlFabricListMain)
    ''' <summary>
    ''' Fabric 版本列表获取的主协调函数。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，用于报告进度和设置结果</param>
    ''' <remarks>
    ''' 处理流程：
    ''' 步骤1：获取用户数据源偏好设置
    ''' - 读取 ToolDownloadVersion 配置值
    ''' - 根据设置决定数据源使用策略
    ''' 
    ''' 步骤2：选择数据源策略
    ''' - Case 0：国内用户，优先使用 BMCLAPI 镜像源
    ''' - Case 1：国外用户，优先使用官方源
    ''' - Case Else：默认策略，优先使用官方源
    ''' 
    ''' 步骤3：执行数据源加载
    ''' - 使用 DlSourceLoader 协调多个数据源
    ''' - 设置合理的超时时间防止长时间等待
    ''' - 支持强制重启机制
    ''' 
    ''' 步骤4：结果处理
    ''' - 成功获取数据后直接传递给调用者
    ''' - 所有数据源失败时抛出异常
    ''' </remarks>
    Private Sub DlFabricListMain(Loader As LoaderTask(Of Integer, DlFabricListResult))
        '根据用户设置选择数据源策略
        Select Case Setup.Get("ToolDownloadVersion")
            Case 0
                '国内用户策略：优先使用 BMCLAPI（30s），失败后使用官方源（90s）
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListBmclapiLoader, 30),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListOfficialLoader, 30 + 60)
                }, Loader.IsForceRestarting)
            Case 1
                '国外用户策略：优先使用官方源（5s），失败后使用 BMCLAPI（35s）
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListOfficialLoader, 5),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListBmclapiLoader, 5 + 30)
                }, Loader.IsForceRestarting)
            Case Else
                '默认策略：优先使用官方源（60s），失败后使用 BMCLAPI（120s）
                DlSourceLoader(Loader, New List(Of KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)) From {
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListOfficialLoader, 60),
                    New KeyValuePair(Of LoaderTask(Of Integer, DlFabricListResult), Integer)(DlFabricListBmclapiLoader, 60 + 60)
                }, Loader.IsForceRestarting)
        End Select
    End Sub

    ''' <summary>
    ''' Fabric 列表，官方源。
    ''' </summary>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 从 Fabric 官方元数据服务器获取最新版本信息
    ''' - 提供 game、loader、installer 三类版本数据
    ''' - 支持实时获取官方最新发布版本
    ''' 
    ''' 主要功能：
    ''' 1. HTTP 请求：向 Fabric 官方元数据服务器发送请求
    ''' 2. JSON 解析：解析返回的 JSON 格式版本数据
    ''' 3. 数据验证：检查必要字段是否存在
    ''' 4. 结果封装：将原始 JSON 数据封装到结果结构中
    ''' 
    ''' 数据结构说明：
    ''' - game：Minecraft 游戏版本兼容性信息
    ''' - loader：Fabric 加载器版本信息
    ''' - installer：Fabric 安装器版本信息
    ''' - 每个分类包含版本号、稳定性、发布时间等元数据
    ''' 
    ''' 异常处理：
    ''' - 网络请求失败时抛出异常
    ''' - 数据格式错误时抛出解析异常
    ''' - 缺少必要字段时抛出验证异常
    ''' </remarks>
    Public DlFabricListOfficialLoader As New LoaderTask(Of Integer, DlFabricListResult)("DlFabricList Official", AddressOf DlFabricListOfficialMain)
    ''' <summary>
    ''' 从 Fabric 官方元数据服务器获取版本列表的主函数。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，用于报告进度和设置结果</param>
    ''' <remarks>
    ''' 处理流程：
    ''' 步骤1：发送 HTTP 请求获取 Fabric 元数据
    ''' - 使用 NetRequestByClientRetry 进行重试机制
    ''' - 目标 URL：https://meta.fabricmc.net/v2/versions
    ''' - 要求返回 JSON 格式数据
    ''' 
    ''' 步骤2：数据验证
    ''' - 检查 game 字段是否存在（Minecraft 版本兼容性）
    ''' - 检查 loader 字段是否存在（Fabric 加载器版本）
    ''' - 检查 installer 字段是否存在（Fabric 安装器版本）
    ''' - 任一字段缺失则抛出异常
    ''' 
    ''' 步骤3：结果封装
    ''' - 标记为官方数据源（IsOfficial = True）
    ''' - 设置来源名称为 "Fabric 官方源"
    ''' - 将原始 JSON 数据直接赋值给 Value 属性
    ''' - 保留完整的元数据结构供后续处理
    ''' </remarks>
    Private Sub DlFabricListOfficialMain(Loader As LoaderTask(Of Integer, DlFabricListResult))
        '发送 HTTP 请求获取 Fabric 元数据，要求返回 JSON 格式
        Dim Result As JObject = GetJson(NetRequestByClientRetry("https://meta.fabricmc.net/v2/versions", RequireJson:=True))
        Try
            '创建输出结果对象，标记为官方数据源并设置来源名称
            Dim Output = New DlFabricListResult With {.IsOfficial = True, .SourceName = "Fabric 官方源", .Value = Result}
            '数据验证：检查必要字段是否存在
            'game：Minecraft 版本兼容性信息，loader：Fabric 加载器版本，installer：Fabric 安装器版本
            If Output.Value("game") Is Nothing OrElse Output.Value("loader") Is Nothing OrElse Output.Value("installer") Is Nothing Then Throw New Exception("获取到的列表缺乏必要项")
            '设置加载器输出结果
            Loader.Output = Output
        Catch ex As Exception
            '异常处理：包装原始异常并重新抛出，包含原始响应数据用于调试
            Throw New Exception("Fabric 官方源版本列表解析失败（" & Result.ToString & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' Fabric 列表，BMCLAPI。
    ''' </summary>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 从 BMCLAPI 镜像源获取 Fabric 版本信息
    ''' - 提供与官方源相同的数据结构（game、loader、installer）
    ''' - 作为官方源的备用数据源，提高访问稳定性
    ''' 
    ''' 主要功能：
    ''' 1. HTTP 请求：向 BMCLAPI Fabric 元数据接口发送请求
    ''' 2. JSON 解析：解析返回的 JSON 格式版本数据
    ''' 3. 数据验证：检查必要字段是否存在
    ''' 4. 结果封装：将原始 JSON 数据封装到结果结构中
    ''' 
    ''' 数据源特点：
    ''' - 镜像官方 Fabric 元数据服务器数据
    ''' - 提供与官方源相同的 API 接口格式
    ''' - 在中国大陆地区访问速度更快
    ''' 
    ''' 异常处理：
    ''' - 网络请求失败时抛出异常
    ''' - 数据格式错误时抛出解析异常
    ''' - 缺少必要字段时抛出验证异常
    ''' </remarks>
    Public DlFabricListBmclapiLoader As New LoaderTask(Of Integer, DlFabricListResult)("DlFabricList Bmclapi", AddressOf DlFabricListBmclapiMain)
    ''' <summary>
    ''' 从 BMCLAPI 镜像源获取 Fabric 版本列表的主函数。
    ''' </summary>
    ''' <param name="Loader">加载器任务对象，用于报告进度和设置结果</param>
    ''' <remarks>
    ''' 处理流程：
    ''' 步骤1：发送 HTTP 请求获取 BMCLAPI Fabric 元数据
    ''' - 使用 NetRequestByClientRetry 进行重试机制
    ''' - 目标 URL：https://bmclapi2.bangbang93.com/fabric-meta/v2/versions
    ''' - 要求返回 JSON 格式数据
    ''' 
    ''' 步骤2：数据验证
    ''' - 检查 game 字段是否存在（Minecraft 版本兼容性）
    ''' - 检查 loader 字段是否存在（Fabric 加载器版本）
    ''' - 检查 installer 字段是否存在（Fabric 安装器版本）
    ''' - 任一字段缺失则抛出异常
    ''' 
    ''' 步骤3：结果封装
    ''' - 标记为非官方数据源（IsOfficial = False）
    ''' - 设置来源名称为 "BMCLAPI"
    ''' - 将原始 JSON 数据直接赋值给 Value 属性
    ''' - 保留完整的元数据结构供后续处理
    ''' </remarks>
    Private Sub DlFabricListBmclapiMain(Loader As LoaderTask(Of Integer, DlFabricListResult))
        '发送 HTTP 请求获取 BMCLAPI Fabric 元数据，要求返回 JSON 格式
        Dim Result As JObject = GetJson(NetRequestByClientRetry("https://bmclapi2.bangbang93.com/fabric-meta/v2/versions", RequireJson:=True))
        Try
            '创建输出结果对象，标记为非官方数据源并设置来源名称
            Dim Output = New DlFabricListResult With {.IsOfficial = False, .SourceName = "BMCLAPI", .Value = Result}
            '数据验证：检查必要字段是否存在
            'game：Minecraft 版本兼容性信息，loader：Fabric 加载器版本，installer：Fabric 安装器版本
            If Output.Value("game") Is Nothing OrElse Output.Value("loader") Is Nothing OrElse Output.Value("installer") Is Nothing Then Throw New Exception("获取到的列表缺乏必要项")
            '设置加载器输出结果
            Loader.Output = Output
        Catch ex As Exception
            '异常处理：包装原始异常并重新抛出，包含原始响应数据用于调试
            Throw New Exception("Fabric BMCLAPI 版本列表解析失败（" & Result.ToString & "）", ex)
        End Try
    End Sub

    ''' <summary>
    ''' Fabric API 列表，官方源。
    ''' </summary>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 获取 Fabric API 模组的版本列表和下载信息
    ''' - 使用 CurseForge 平台作为数据源
    ''' - 提供完整的模组文件信息（版本、下载链接、依赖等）
    ''' 
    ''' 主要功能：
    ''' 1. 模组搜索：通过模组名称 "fabric-api" 在 CurseForge 平台搜索
    ''' 2. 文件获取：获取模组的所有可用文件版本
    ''' 3. 数据解析：解析模组元数据和下载信息
    ''' 4. 结果封装：将文件列表封装到 CompFile 结构中
    ''' 
    ''' 数据源说明：
    ''' - 使用 CurseForge API 作为官方数据源
    ''' - 模组 ID：fabric-api（字符串标识符）
    ''' - 非第三方镜像源（False 表示官方源）
    ''' 
    ''' 返回数据结构：
    ''' - List(Of CompFile)：模组文件列表
    ''' - 每个 CompFile 包含版本号、文件名、下载链接等信息
    ''' </remarks>
    Public DlFabricApiLoader As New LoaderTask(Of Integer, List(Of CompFile))("Fabric API List Loader",
        '使用 Lambda 表达式创建异步任务，调用 CompFilesGet 获取 Fabric API 文件列表
        '参数说明："fabric-api" - 模组名称，False - 使用官方源而非第三方镜像
        Sub(Task As LoaderTask(Of Integer, List(Of CompFile))) Task.Output = CompFilesGet("fabric-api", False))

    ''' <summary>
    ''' OptiFabric 列表，官方源。
    ''' </summary>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 获取 OptiFabric 模组的版本列表和下载信息
    ''' - 使用 CurseForge 平台作为数据源
    ''' - 提供 OptiFine 与 Fabric 兼容的模组文件
    ''' 
    ''' 主要功能：
    ''' 1. 模组搜索：通过模组 ID "322385" 在 CurseForge 平台搜索
    ''' 2. 文件获取：获取模组的所有可用文件版本
    ''' 3. 数据解析：解析模组元数据和下载信息
    ''' 4. 结果封装：将文件列表封装到 CompFile 结构中
    ''' 
    ''' 数据源说明：
    ''' - 使用 CurseForge API 作为官方数据源
    ''' - 模组 ID：322385（数字标识符）
    ''' - 第三方镜像源（True 表示使用第三方镜像）
    ''' - 提供更快的下载速度和更好的可用性
    ''' 
    ''' 模组功能：
    ''' - 允许在 Fabric 环境下使用 OptiFine
    ''' - 提供 OptiFine 的兼容性支持
    ''' - 需要与对应版本的 OptiFine 配合使用
    ''' 
    ''' 返回数据结构：
    ''' - List(Of CompFile)：模组文件列表
    ''' - 每个 CompFile 包含版本号、文件名、下载链接等信息
    ''' </remarks>
    Public DlOptiFabricLoader As New LoaderTask(Of Integer, List(Of CompFile))("OptiFabric List Loader",
        '使用 Lambda 表达式创建异步任务，调用 CompFilesGet 获取 OptiFabric 文件列表
        '参数说明："322385" - 模组数字 ID，True - 使用第三方镜像源提高下载速度
        Sub(Task As LoaderTask(Of Integer, List(Of CompFile))) Task.Output = CompFilesGet("322385", True))

#End Region

#Region "DlMod | Mod 镜像源请求"

    ''' <summary>
    ''' 对可能涉及 Mod 镜像源的请求进行处理，返回 JToken。
    ''' 调用 NetRequest，会进行重试。
    ''' </summary>
    ''' <param name="Url">原始请求 URL</param>
    ''' <param name="Method">HTTP 请求方法（默认为 GET）</param>
    ''' <param name="Content">请求内容（用于 POST 等请求）</param>
    ''' <param name="ContentType">内容类型（如 application/json）</param>
    ''' <returns>解析后的 JSON 数据（JToken 类型）</returns>
    ''' <remarks>
    ''' 扩展功能概述：
    ''' - 智能处理 Mod 相关的镜像源请求
    ''' - 根据用户设置选择优先使用的数据源
    ''' - 提供多源重试机制，确保请求成功率
    ''' - 支持自定义 HTTP 方法和内容类型
    ''' 
    ''' 主要功能：
    ''' 1. URL 转换：通过 DlSourceModGet 获取镜像源 URL
    ''' 2. 策略选择：根据 ToolDownloadMod 设置决定请求顺序
    ''' 3. 超时控制：为每个数据源设置合理的超时时间
    ''' 4. 异常处理：收集所有异常信息，提供详细的错误报告
    ''' 5. JSON 解析：自动解析返回的 JSON 数据
    ''' 
    ''' 数据源策略（ToolDownloadMod）：
    ''' - Case 0：优先使用镜像源（MCIM），10s+10s 超时，失败后使用官方源 30s
    ''' - Case 1：优先使用官方源 10s，失败后使用镜像源 10s，再失败使用官方源 30s，最后镜像源 30s
    ''' - Case Else：优先使用官方源 10s+30s，失败后使用镜像源 30s
    ''' 
    ''' 无镜像源情况：
    ''' - 仅使用原始 URL，设置 10s+30s 超时时间
    ''' 
    ''' 异常处理：
    ''' - 收集所有数据源的异常信息
    ''' - 按顺序尝试每个数据源直到成功
    ''' - 全部失败时抛出包含所有异常信息的异常
    ''' </remarks>
    Public Function DlModRequest(Url As String, Optional Method As HttpMethod = Nothing,
                                 Optional Content As String = Nothing, Optional ContentType As String = Nothing) As JToken
        '创建 URL 列表，存储要尝试的请求地址和对应的超时时间（秒）
        '使用 KeyValuePair 结构，Key 为 URL，Value 为超时时间（秒）
        Dim Urls As New List(Of KeyValuePair(Of String, Integer))
        
        '通过 DlSourceModGet 获取镜像源 URL，如果返回不同 URL 表示存在镜像源
        Dim McimUrl As String = DlSourceModGet(Url)
        
        '判断是否存在可用的镜像源
        If McimUrl <> Url Then
            '存在镜像源，根据用户设置选择请求策略
            Select Case Setup.Get("ToolDownloadMod")
                Case 0
                    '策略 0：优先使用镜像源
                    '添加镜像源 URL，设置 10 秒超时（重试两次）
                    Urls.Add(New KeyValuePair(Of String, Integer)(McimUrl, 10))
                    Urls.Add(New KeyValuePair(Of String, Integer)(McimUrl, 10))
                    '添加官方源 URL，设置 30 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(Url, 30))
                Case 1
                    '策略 1：优先使用官方源
                    '添加官方源 URL，设置 10 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(Url, 10)) '至少 10s，要不然有时候远端服务器来不及完成
                    '添加镜像源 URL，设置 10 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(McimUrl, 10))
                    '再次添加官方源 URL，设置 30 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(Url, 30))
                    '再次添加镜像源 URL，设置 30 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(McimUrl, 30))
                Case Else
                    '默认策略：优先使用官方源
                    '添加官方源 URL，设置 10 秒+30 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(Url, 10))
                    Urls.Add(New KeyValuePair(Of String, Integer)(Url, 30))
                    '添加镜像源 URL，设置 30 秒超时
                    Urls.Add(New KeyValuePair(Of String, Integer)(McimUrl, 30))
            End Select
        Else
            '不存在镜像源，仅使用原始 URL
            '添加官方源 URL，设置 10 秒+30 秒超时时间
            Urls.Add(New KeyValuePair(Of String, Integer)(Url, 10))
            Urls.Add(New KeyValuePair(Of String, Integer)(Url, 30))
        End If
        
        '创建异常信息字符串，用于收集所有数据源的异常信息
        Dim Exs As String = ""
        
        '遍历所有 URL，按顺序尝试请求
        For Each Source In Urls
            Try
                '尝试发送 HTTP 请求并解析 JSON 数据
                'NetRequestByClient：发送 HTTP 请求，Source.Key 为 URL，Source.Value 为超时时间（毫秒）
                'GetJson：解析返回的 JSON 数据
                Return GetJson(NetRequestByClient(Source.Key, Method, Content, ContentType, Timeout:=Source.Value * 1000, Encoding:=Encoding.UTF8, RequireJson:=True))
            Catch ex As Exception
                '请求失败，收集异常信息
                '将异常信息添加到异常字符串，每个异常占一行
                Exs += ex.Message + vbCrLf
            End Try
        Next
        
        '所有数据源都失败，抛出包含所有异常信息的异常
        Throw New Exception(Exs)
    End Function

#End Region

#Region "DlSource | 镜像下载源"

    Private DlPreferMojang As Boolean = False
    ''' <summary>
    ''' 下载文件（而非获取版本列表）的时候，是否优先使用官方源。
    ''' </summary>
    ''' <remarks>
    ''' 功能说明：
    ''' - 根据 ToolDownloadSource 设置决定是否优先使用 Mojang 官方源
    ''' - 支持三种设置模式：
    '''   * 设置值 = 2：强制优先使用官方源
    '''   * 设置值 = 1 且 DlPreferMojang = True：优先使用官方源
    '''   * 其他情况：不优先使用官方源
    ''' 
    ''' 使用场景：
    ''' - 下载 Minecraft 核心文件（jar、json）
    ''' - 下载 Libraries 依赖库文件
    ''' - 下载 Assets 资源文件
    ''' - 其他非版本列表获取的文件下载操作
    ''' 
    ''' 优先级逻辑：
    ''' - 用户明确设置优先使用官方源时返回 True
    ''' - 用户设置智能选择且当前标记为优先官方源时返回 True
    ''' - 其他情况返回 False，优先使用镜像源
    ''' </remarks>
    Public ReadOnly Property DlSourcePreferMojang As Boolean
        Get
            '获取 ToolDownloadSource 设置值，决定文件下载时的数据源优先级
            '设置值 = 2：强制优先使用官方源
            '设置值 = 1：智能选择，结合 DlPreferMojang 标记决定
            Return Setup.Get("ToolDownloadSource") = 2 OrElse (Setup.Get("ToolDownloadSource") = 1 AndAlso DlPreferMojang)
        End Get
    End Property
    ''' <summary>
    ''' 下载文件（而非获取版本列表）的时候，根据是否优先使用官方源决定使用 Url 的顺序。
    ''' </summary>
    ''' <param name="OfficialUrls">官方源的 URL 列表</param>
    ''' <param name="MirrorUrls">镜像源的 URL 列表</param>
    ''' <returns>按优先级排序的 URL 列表</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 根据 DlSourcePreferMojang 属性决定 URL 列表的合并顺序
    ''' - 支持官方源优先和镜像源优先两种策略
    ''' 
    ''' 合并策略：
    ''' - 当 DlSourcePreferMojang = True 时：官方源在前，镜像源在后
    ''' - 当 DlSourcePreferMojang = False 时：镜像源在前，官方源在后
    ''' 
    ''' 使用场景：
    ''' - 下载游戏核心文件时的 URL 列表排序
    ''' - Libraries 依赖库文件的 URL 列表排序
    ''' - Assets 资源文件的 URL 列表排序
    ''' 
    ''' 注意事项：
    ''' - 使用 Union 方法确保结果中无重复 URL
    ''' - 返回的列表按优先级从高到低排序
    ''' - 下载时会依次尝试列表中的每个 URL
    ''' </remarks>
    Public Function DlSourceOrder(OfficialUrls As IEnumerable(Of String), MirrorUrls As IEnumerable(Of String)) As IEnumerable(Of String)
        '根据 DlSourcePreferMojang 属性决定 URL 列表的合并顺序
        'True：官方源优先，先合并官方源再合并镜像源
        'False：镜像源优先，先合并镜像源再合并官方源
        Return If(DlSourcePreferMojang, OfficialUrls.Union(MirrorUrls), MirrorUrls.Union(OfficialUrls))
    End Function
    ''' <summary>
    ''' 获取版本列表（而非下载文件）的时候，是否优先使用官方源。
    ''' </summary>
    ''' <remarks>
    ''' 功能说明：
    ''' - 根据 ToolDownloadVersion 设置决定是否优先使用 Mojang 官方源获取版本列表
    ''' - 与 DlSourcePreferMojang 类似，但专门用于版本列表获取场景
    ''' 
    ''' 设置模式：
    ''' - 设置值 = 2：强制优先使用官方源获取版本列表
    ''' - 设置值 = 1 且 DlPreferMojang = True：优先使用官方源获取版本列表
    ''' - 其他情况：不优先使用官方源获取版本列表
    ''' 
    ''' 使用场景：
    ''' - 获取 Minecraft 版本列表
    ''' - 获取 Forge 版本列表
    ''' - 获取 Fabric 版本列表
    ''' - 获取 LiteLoader 版本列表
    ''' - 其他版本信息获取操作
    ''' 
    ''' 与 DlSourcePreferMojang 的区别：
    ''' - 本属性专门用于版本列表获取
    ''' - DlSourcePreferMojang 用于文件下载
    ''' - 两者使用不同的设置项（ToolDownloadVersion vs ToolDownloadSource）
    ''' </remarks>
    Public ReadOnly Property DlVersionListPreferMojang As Boolean
        Get
            '获取 ToolDownloadVersion 设置值，决定版本列表获取时的数据源优先级
            '设置值 = 2：强制优先使用官方源
            '设置值 = 1：智能选择，结合 DlPreferMojang 标记决定
            Return Setup.Get("ToolDownloadVersion") = 2 OrElse (Setup.Get("ToolDownloadVersion") = 1 AndAlso DlPreferMojang)
        End Get
    End Property
    ''' <summary>
    ''' 获取版本列表（而非下载文件）的时候，根据是否优先使用官方源决定使用 Url 的顺序。
    ''' </summary>
    ''' <param name="OfficialUrls">官方源的 URL 列表</param>
    ''' <param name="MirrorUrls">镜像源的 URL 列表</param>
    ''' <returns>按优先级排序的 URL 列表</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 根据 DlVersionListPreferMojang 属性决定 URL 列表的合并顺序
    ''' - 与 DlSourceOrder 类似，但专门用于版本列表获取场景
    ''' 
    ''' 合并策略：
    ''' - 当 DlVersionListPreferMojang = True 时：官方源在前，镜像源在后
    ''' - 当 DlVersionListPreferMojang = False 时：镜像源在前，官方源在后
    ''' 
    ''' 使用场景：
    ''' - 获取 Minecraft 版本列表时的 URL 排序
    ''' - 获取 Forge 版本列表时的 URL 排序
    ''' - 获取 Fabric 版本列表时的 URL 排序
    ''' - 获取 LiteLoader 版本列表时的 URL 排序
    ''' 
    ''' 与 DlSourceOrder 的区别：
    ''' - 本函数专门用于版本列表获取
    ''' - DlSourceOrder 用于文件下载
    ''' - 两者使用不同的优先级属性
    ''' 
    ''' 注意事项：
    ''' - 使用 Union 方法确保结果中无重复 URL
    ''' - 返回的列表按优先级从高到低排序
    ''' - 获取版本列表时会依次尝试列表中的每个 URL
    ''' </remarks>
    Public Function DlVersionListOrder(OfficialUrls As IEnumerable(Of String), MirrorUrls As IEnumerable(Of String)) As IEnumerable(Of String)
        '根据 DlVersionListPreferMojang 属性决定 URL 列表的合并顺序
        'True：官方源优先，先合并官方源再合并镜像源
        'False：镜像源优先，先合并镜像源再合并官方源
        Return If(DlVersionListPreferMojang, OfficialUrls.Union(MirrorUrls), MirrorUrls.Union(OfficialUrls))
    End Function


    ''' <summary>
    ''' 下载 Assets 文件。
    ''' </summary>
    ''' <param name="Original">原始 Assets 文件 URL</param>
    ''' <returns>按优先级排序的 Assets 文件 URL 列表</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 为 Assets 文件下载生成官方源和镜像源的 URL 列表
    ''' - 根据 DlSourcePreferMojang 设置决定 URL 优先级顺序
    ''' 
    ''' URL 处理逻辑：
    ''' 1. 首先将 HTTP 协议替换为 HTTPS 协议，确保安全性
    ''' 2. 生成镜像源 URL，将官方域名替换为 BMCLAPI 镜像域名
    ''' 3. 调用 DlSourceOrder 函数根据设置决定最终顺序
    ''' 
    ''' 支持的官方域名替换：
    ''' - https://piston-data.mojang.com → https://bmclapi2.bangbang93.com/assets
    ''' - https://piston-meta.mojang.com → https://bmclapi2.bangbang93.com/assets  
    ''' - https://resources.download.minecraft.net → https://bmclapi2.bangbang93.com/assets
    ''' 
    ''' 使用场景：
    ''' - 下载游戏资源文件（图片、声音等）
    ''' - 获取 Assets 索引文件
    ''' - 资源文件完整性检查时的 URL 生成
    ''' 
    ''' 返回结果：
    ''' - 始终包含原始 URL（已转换为 HTTPS）
    ''' - 包含对应的镜像源 URL
    ''' - 根据用户设置决定官方源和镜像源的顺序
    ''' </remarks>
    Public Function DlSourceAssetsGet(Original As String) As IEnumerable(Of String)
        '将 HTTP 协议替换为 HTTPS 协议，确保下载安全性
        'resources.download.minecraft.net 是 Assets 文件的主要域名
        Original = Original.Replace("http://resources.download.minecraft.net", "https://resources.download.minecraft.net")
        
        '调用 DlSourceOrder 函数生成 URL 列表
        '参数1：官方源列表（仅包含原始 URL）
        '参数2：镜像源列表（将官方域名替换为 BMCLAPI 镜像域名）
        Return DlSourceOrder(
            {Original},
            {Original.
                Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/assets").
                Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/assets").
                Replace("https://resources.download.minecraft.net", "https://bmclapi2.bangbang93.com/assets")
            })
    End Function
    ''' <summary>
    ''' 下载 Libraries 文件。
    ''' </summary>
    ''' <param name="Original">原始 Libraries 文件 URL</param>
    ''' <returns>按优先级排序的 Libraries 文件 URL 列表</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 为 Libraries 文件下载生成官方源和镜像源的 URL 列表
    ''' - 根据库的类型（Forge/Fabric/NeoForged 或其他）采用不同的镜像策略
    ''' - 支持 Maven 仓库和 Libraries 仓库两种镜像路径
    ''' 
    ''' 特殊处理逻辑：
    ''' - 对于 minecraftforge、fabricmc、neoforged 等模组加载器的库：
    '''   * 不添加官方源，仅返回镜像源
    '''   * 提供 Maven 和 Libraries 两个镜像路径作为备选
    ''' - 对于其他类型的库：
    '''   * 根据 DlSourcePreferMojang 设置决定官方源和镜像源的顺序
    '''   * 提供 Maven 和 Libraries 两个镜像路径
    ''' 
    ''' 镜像域名替换：
    ''' - https://piston-data.mojang.com → https://bmclapi2.bangbang93.com/maven 或 /libraries
    ''' - https://piston-meta.mojang.com → https://bmclapi2.bangbang93.com/maven 或 /libraries
    ''' - https://libraries.minecraft.net → https://bmclapi2.bangbang93.com/maven 或 /libraries
    ''' 
    ''' 使用场景：
    ''' - 下载 Minecraft 核心库文件
    ''' - 下载 Forge 相关库文件
    ''' - 下载 Fabric 相关库文件
    ''' - 下载 NeoForged 相关库文件
    ''' - 其他第三方依赖库文件
    ''' 
    ''' 返回结果：
    ''' - 对于模组加载器库：仅返回镜像源 URL 列表
    ''' - 对于其他库：根据设置返回官方源优先或镜像源优先的 URL 列表
    ''' - 每个库都提供 Maven 和 Libraries 两个镜像路径作为备选
    ''' </remarks>
    Public Function DlSourceLibraryGet(Original As String) As IEnumerable(Of String)
        '检查 URL 是否包含模组加载器相关关键字
        'minecraftforge：Minecraft Forge
        'fabricmc：Fabric 加载器
        'neoforged：NeoForged 加载器
        If {"minecraftforge", "fabricmc", "neoforged"}.Any(Function(k) Original.Contains(k)) Then '不添加原版源
            '对于模组加载器的库，仅返回镜像源，不提供官方源
            '提供 Maven 和 Libraries 两个镜像路径作为备选
            Return {
                'Maven 仓库镜像路径
                Original.
                    Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven").
                    Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven").
                    Replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"),
                'Libraries 仓库镜像路径
                Original.
                    Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/libraries").
                    Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/libraries").
                    Replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries")
            }
        Else
            '对于其他类型的库，根据用户设置决定官方源和镜像源的顺序
            '提供 Maven 和 Libraries 两个镜像路径作为备选
            Return DlSourceOrder(
                {Original}, '官方源（仅原始 URL）
                {Original.
                    Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven").
                    Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven").
                    Replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"), 'Maven 镜像路径
                 Original.
                    Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/libraries").
                    Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/libraries").
                    Replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries") 'Libraries 镜像路径
                })
        End If
    End Function
    ''' <summary>
    ''' 下载 Launcher 或 Meta 文件。
    ''' 不应使用它来获取版本列表（因为它只使用文件下载源设置来决定源顺序）。
    ''' </summary>
    ''' <param name="Original">原始 Launcher 或 Meta 文件 URL</param>
    ''' <returns>按优先级排序的 Launcher 或 Meta 文件 URL 列表</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 为 Launcher 和 Meta 文件下载生成官方源和镜像源的 URL 列表
    ''' - 根据 DlSourcePreferMojang 设置决定 URL 优先级顺序
    ''' - 专门用于启动器相关文件的下载
    ''' 
    ''' 重要警告：
    ''' - 本函数不应被用于获取版本列表
    ''' - 它使用文件下载源设置（DlSourcePreferMojang）而非版本列表设置
    ''' - 获取版本列表请使用 DlVersionListOrder 函数
    ''' 
    ''' 输入验证：
    ''' - 如果 Original 参数为 Nothing，抛出异常"无对应的 json 下载地址"
    ''' - 确保调用方提供了有效的 URL
    ''' 
    ''' 镜像域名替换：
    ''' - https://piston-data.mojang.com → https://bmclapi2.bangbang93.com
    ''' - https://piston-meta.mojang.com → https://bmclapi2.bangbang93.com
    ''' - https://launcher.mojang.com → https://bmclapi2.bangbang93.com
    ''' - https://launchermeta.mojang.com → https://bmclapi2.bangbang93.com
    ''' 
    ''' 使用场景：
    ''' - 下载游戏版本 JSON 元数据文件
    ''' - 下载启动器相关配置文件
    ''' - 获取游戏版本信息文件
    ''' - 其他 Launcher/Meta 相关文件下载
    ''' 
    ''' 返回结果：
    ''' - 始终包含原始 URL
    ''' - 包含对应的镜像源 URL
    ''' - 根据用户设置决定官方源和镜像源的顺序
    ''' </remarks>
    Public Function DlSourceLauncherOrMetaGet(Original As String) As IEnumerable(Of String)
        '输入验证：确保提供了有效的 URL
        '如果 Original 为 Nothing，抛出异常提示无下载地址
        If Original Is Nothing Then Throw New Exception("无对应的 json 下载地址")
        
        '调用 DlSourceOrder 函数生成 URL 列表
        '参数1：官方源列表（仅包含原始 URL）
        '参数2：镜像源列表（将官方域名替换为 BMCLAPI 镜像域名）
        Return DlSourceOrder(
            {Original},
            {Original.
                Replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com").
                Replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com").
                Replace("https://launcher.mojang.com", "https://bmclapi2.bangbang93.com").
                Replace("https://launchermeta.mojang.com", "https://bmclapi2.bangbang93.com")
            })
    End Function

    ''' <summary>
    ''' Mod 下载源。
    ''' </summary>
    ''' <param name="Original">原始 Mod 下载 URL</param>
    ''' <returns>替换后的 Mod 镜像源 URL</returns>
    ''' <remarks>
    ''' 功能说明：
    ''' - 将 Mod 下载的原始 URL 替换为镜像源 URL
    ''' - 专门用于 Modrinth 和 CurseForge 两个主流模组平台的镜像
    ''' - 使用国内的 MCI Mirror 镜像源，提高下载速度和稳定性
    ''' 
    ''' 支持的模组平台：
    ''' - Modrinth：开源模组平台，支持 API 和 CDN 域名
    ''' - CurseForge：主流模组平台，支持 API 和 CDN 域名
    ''' 
    ''' 域名替换规则：
    ''' - api.modrinth.com → mod.mcimirror.top/modrinth
    ''' - staging-api.modrinth.com → mod.mcimirror.top/modrinth（测试环境）
    ''' - cdn.modrinth.com → mod.mcimirror.top（CDN 资源）
    ''' - api.curseforge.com → mod.mcimirror.top/curseforge
    ''' - edge.forgecdn.net → mod.mcimirror.top（CurseForge CDN）
    ''' - mediafilez.forgecdn.net → mod.mcimirror.top（CurseForge 媒体文件）
    ''' - media.forgecdn.net → mod.mcimirror.top（CurseForge 媒体资源）
    ''' 
    ''' 镜像源特点：
    ''' - 使用国内服务器，访问速度更快
    ''' - 提供 Modrinth 和 CurseForge 的完整镜像
    ''' - 支持 API 调用和文件下载的镜像
    ''' 
    ''' 使用场景：
    ''' - 下载 Mod 文件时的 URL 替换
    ''' - 获取 Mod 元数据信息时的 API 调用
    ''' - 模组管理器的镜像源支持
    ''' 
    ''' 注意事项：
    ''' - 本函数仅返回单个镜像 URL，不提供多个备选
    ''' - 如果原始 URL 不匹配任何已知域名，将返回原始 URL
    ''' - 镜像源的可用性取决于第三方服务状态
    ''' </remarks>
    Public Function DlSourceModGet(Original As String) As String
        '依次替换各个模组平台的域名
        '使用 MCI Mirror 作为国内镜像源
        Return Original.
            Replace("api.modrinth.com", "mod.mcimirror.top/modrinth"). 'Modrinth API 镜像
            Replace("staging-api.modrinth.com", "mod.mcimirror.top/modrinth"). 'Modrinth 测试 API 镜像
            Replace("cdn.modrinth.com", "mod.mcimirror.top"). 'Modrinth CDN 镜像
            Replace("api.curseforge.com", "mod.mcimirror.top/curseforge"). 'CurseForge API 镜像
            Replace("edge.forgecdn.net", "mod.mcimirror.top"). 'CurseForge CDN 主镜像
            Replace("mediafilez.forgecdn.net", "mod.mcimirror.top"). 'CurseForge 媒体文件镜像
            Replace("media.forgecdn.net", "mod.mcimirror.top") 'CurseForge 媒体资源镜像
    End Function

    'Loader 自动切换
    Private Sub DlSourceLoader(Of InputType, OutputType)(MainLoader As LoaderTask(Of InputType, OutputType),
                                                         LoaderList As List(Of KeyValuePair(Of LoaderTask(Of InputType, OutputType), Integer)),
                                                         Optional IsForceRestart As Boolean = False)
        Dim WaitCycle As Integer = 0
        Do While True
            '检查状态
            Dim BeforeLoadersAllFailed As Boolean = True
            For Each SubLoader In LoaderList
                If WaitCycle = 0 Then '判断是否可以不加载，直接使用已经加载好的结果
                    If IsForceRestart Then Continue For '强制刷新，不行
                    If (SubLoader.Key.Input Is Nothing Xor MainLoader.Input Is Nothing) OrElse
                       (SubLoader.Key.Input IsNot Nothing AndAlso Not SubLoader.Key.Input.Equals(MainLoader.Input)) Then Continue For '父子加载器的输入不一样，也不行
                End If
                If SubLoader.Key.State <> LoadState.Failed Then BeforeLoadersAllFailed = False
                If SubLoader.Key.State = LoadState.Finished Then
                    '检查加载器成功
                    MainLoader.Output = SubLoader.Key.Output
                    DlSourceLoaderAbort(LoaderList)
                    Return
                ElseIf BeforeLoadersAllFailed Then
                    '此前的加载器全部失败，直接启动后续加载器
                    If WaitCycle < SubLoader.Value * 100 Then WaitCycle = SubLoader.Value * 100
                End If
            Next
            '第一轮时：既然不直接使用已经加载好的结果，那就启动第一个加载器
            If WaitCycle = 0 Then
                LoaderList.First.Key.Start(MainLoader.Input, IsForceRestart)
                For Each Loader In LoaderList.Skip(1)
                    Loader.Key.State = LoadState.Waiting '将其他源标记为未启动，以确保可以切换下载源（#184）
                Next
            End If
            '检查加载器失败或超时
            For i = 0 To LoaderList.Count - 1
                If WaitCycle <> LoaderList(i).Value * 100 Then Continue For
                If i < LoaderList.Count - 1 AndAlso Not LoaderList.All(Function(l) l.Key.State = LoadState.Failed) Then
                    '若还有下一个源，则启动下一个源
                    LoaderList(i + 1).Key.Start(MainLoader.Input, IsForceRestart)
                Else
                    '若没有，则失败
                    Dim ErrorInfo As Exception = Nothing
                    For ii = 0 To LoaderList.Count - 1
                        LoaderList(ii).Key.Input = Nothing '重置输入，以免以同样的输入“重试加载”时直接失败
                        If LoaderList(ii).Key.Error IsNot Nothing Then
                            If ErrorInfo Is Nothing OrElse LoaderList(ii).Key.Error.Message.Contains("不可用") Then
                                ErrorInfo = LoaderList(ii).Key.Error
                            End If
                        End If
                    Next
                    If ErrorInfo Is Nothing Then ErrorInfo = New TimeoutException("下载源连接超时")
                    DlSourceLoaderAbort(LoaderList)
                    Throw ErrorInfo
                End If
                Exit For
            Next
            '计时
            Thread.Sleep(10)
            WaitCycle += 1
            '检查父加载器中断
            If MainLoader.IsAborted Then
                DlSourceLoaderAbort(LoaderList)
                Return
            End If
        Loop
    End Sub
    Private Sub DlSourceLoaderAbort(Of InputType, OutputType)(LoaderList As List(Of KeyValuePair(Of LoaderTask(Of InputType, OutputType), Integer)))
        For Each Loader In LoaderList
            If Loader.Key.State = LoadState.Loading Then Loader.Key.Abort()
        Next
    End Sub

#End Region

End Module