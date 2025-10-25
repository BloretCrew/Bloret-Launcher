; MyAppVersion 的值会由 Github Actions 自动修改
#define MyAppName "Bloret-Launcher"
#define MyAppVersion "8-Beta"
#define MyAppPublisher "Bloret"
#define MyAppURL "https://launcher.bloret.net/"
#define MyAppExeName "Bloret-Launcher.exe"
#define MyAppAssocName "Java 可执行文件"
#define MyAppAssocExt ".jar"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; 注意：AppId 的值唯一标识此应用程序。不要在其他应用程序的安装程序中使用相同的 AppId 值。
; (若要生成新的 GUID，请在 IDE 中单击 "工具|生成 GUID"。)
AppId={{A9AFE7D1-89A9-47C5-9E1A-003DB3575EB8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; 修改安装目录使用Inno Setup内置宏确保路径正确
DefaultDirName={userappdata}\{#MyAppName}
DisableDirPage=no
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
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; LicenseFile=output\LICENSE
; 移除以下行以在管理安装模式下运行 (为所有用户安装)。
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
OutputDir=.\output
OutputBaseFilename=Bloret Launcher Setup
SetupIconFile=output\bloret.ico
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "output\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\Bloret-Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\cmcl.blank.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\cmcl.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\cmcl.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\cmcl_save.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\servers.dat"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\bloret.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\frpc.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\frpc.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\JavaWrapper.jar"; DestDir: "{app}"; Flags: ignoreversion
; Source: "output\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "output\ui\*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "output\lang\*"; DestDir: "{app}\lang"; Flags: ignoreversion recursesubdirs createallsubdirs
; 注意：不要在任何共享系统文件上使用 "Flags: ignoreversion"

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait