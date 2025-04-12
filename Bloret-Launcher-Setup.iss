; 脚本由 Inno Setup 脚本向导生成。
; 有关创建 Inno Setup 脚本文件的详细信息，请参阅帮助文档！

#define MyAppName "Bloret Launcher"
#define MyAppVersion "5"
#define MyAppPublisher "Bloret"
#define MyAppURL "http://pcfs.top:2"
#define MyAppExeName "Bloret-Launcher.exe"
#define MyAppAssocName "Minecraft Java"
#define MyAppAssocExt ".jar"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; 注意：AppId 的值唯一标识此应用程序。不要在其他应用程序的安装程序中使用相同的 AppId 值。
; (若要生成新的 GUID，请在 IDE 中单击 "工具|生成 GUID"。)
AppId={{265F7FFE-9C08-4DE6-AB01-25B2923911E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Blotet-Launcher
DisableDirPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
; "ArchitecturesAllowed=x64compatible" 指定安装程序无法运行
; 除 Arm 上的 x64 和 Windows 11 之外的任何平台上。
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" 要求
; 安装可以在 x64 或 Arm 上的 Windows 11 上以“64 位模式”完成，
; 这意味着它应该使用本机 64 位 Program Files 目录和
; 注册表的 64 位视图。
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
DisableProgramGroupPage=yes
LicenseFile=g:\Work\git\Bloret-Launcher\LICENSE
; 取消注释以下行以在非管理安装模式下运行 (仅为当前用户安装)。
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=g:\Work\git\Bloret-Launcher\output
OutputBaseFilename=Bloret Launcher Setup
SetupIconFile=g:\Work\git\Bloret-Launcher\icons\bloret.ico
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "g:\Work\git\Bloret-Launcher\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\icons\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "g:\Work\git\Bloret-Launcher\ui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "g:\Work\git\Bloret-Launcher\cmcl.blank.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\cmcl.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\cmcl.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\cmcl_save.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "g:\Work\git\Bloret-Launcher\servers.dat"; DestDir: "{app}"; Flags: ignoreversion
; 注意：不要在任何共享系统文件上使用 "Flags: ignoreversion"

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

