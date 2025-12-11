; MinecraftFRP Inno Setup 安装脚本
; 替代原来的 src_installer Python安装程序

#define MyAppName "MinecraftFRP"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "MitaHill"
#define MyAppURL "https://github.com/MitaHill/MinecraftFRP"
#define MyAppExeName "launcher.exe"
#define MyAppId "{{8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}"
#ifndef Channel
  #define Channel "stable"
#endif

[Setup]
; 应用信息
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; 安装路径
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; 输出配置 - 所有构建产物先存放在 build/ 目录
OutputDir=build\installer_output
OutputBaseFilename=MinecraftFRP_Setup_{#MyAppVersion}
SetupIconFile=base\logo.ico

; 压缩配置（暂时使用较低压缩以避免文件锁定问题）
Compression=lzma2/ultra64
SolidCompression=yes
; LZMAUseSeparateProcess=yes
; LZMANumBlockThreads=4

; 界面配置
WizardStyle=modern
; WizardImageFile=base\logo.bmp
; WizardSmallImageFile=base\logo_small.bmp
DisableWelcomePage=no

; 卸载配置
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 权限配置
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 其他配置
ArchitecturesInstallIn64BitMode=x64compatible
AllowNoIcons=yes
ChangesEnvironment=no

; 覆盖更新配置（方案一：支持像微信/Chrome那样的覆盖安装）
; 注意：Inno Setup 会自动检测文件占用并提示用户关闭程序
; 无需额外配置，AppId 一致即可实现覆盖安装

[Languages]
; 使用默认英语（Inno Setup 6 不包含简体中文）
; 如需中文，需从 https://jrsoftware.org/files/istrans/ 下载 ChineseSimplified.isl
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式:"; Flags: unchecked
Name: "startupicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "快捷方式:"

[Files]
; 通过预处理器定义动态输入目录，允许外部传入 /DBuildOutput, /DAppDist
; 默认使用相对路径，以避免硬编码绝对路径
#ifndef BuildOutput
  #define BuildOutput "build\\MinecraftFRP_build"
#endif
#ifndef AppDist
  #define AppDist "{#BuildOutput}\\app.dist"
#endif

; Launcher (启动器)
Source: "{#BuildOutput}\\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
; Launcher 依赖目录（Nuitka 非单文件模式）
#ifexist "{#BuildOutput}\\nuitka_launcher\\"
Source: "{#BuildOutput}\\nuitka_launcher\\*"; DestDir: "{app}\\nuitka_launcher"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

; 主应用程序：将整个目录放到 MitaHill-FRP-APP
Source: "{#AppDist}\*"; DestDir: "{app}\MitaHill-FRP-APP"; Flags: ignoreversion recursesubdirs createallsubdirs

; FRP工具和基础文件
; 注意：如果 AppDist 中已经包含了 base，这里可能需要调整，或者保留以覆盖
Source: "base\*"; DestDir: "{app}\base"; Flags: ignoreversion recursesubdirs createallsubdirs

; 配置文件迁移到用户文档
Source: "config\*"; DestDir: "{userdocs}\MitaHillFRP\Config"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist

[Dirs]
; 创建用户文档目录与日志目录
Name: "{userdocs}\MitaHillFRP"; Permissions: users-modify
Name: "{userdocs}\MitaHillFRP\logs"; Permissions: users-modify

[InstallDelete]
; 清理旧版本的日志目录，避免混淆
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\MitaHill-FRP-APP\logs"
Type: filesandordirs; Name: "{app}\app\logs"

[Icons]
; 开始菜单图标 - 指向 Launcher
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startupicon

; 桌面图标 - 指向 Launcher
Name: "{autodesktop}\Minecraft联机工具"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后可选择立即运行 Launcher
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; 保存安装路径到注册表（供launcher使用）
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Code]
var
  ConfigPage: TInputDirWizardPage;
  InstallInfoFile: String;

// 在安装前创建配置页面
procedure InitializeWizard;
begin
  // 欢迎页面后添加说明
  WizardForm.WelcomeLabel2.Caption := 
    'MinecraftFRP 是一个 Minecraft 联机工具，' +
    '可以帮助您轻松实现无公网IP的联机游戏。' + #13#10#13#10 +
    '本程序将在您的电脑上安装 MinecraftFRP。';
end;

// 安装完成后的操作
procedure CurStepChanged(CurStep: TSetupStep);
var
  InstallInfo: String;
  DocsPath: String;
  InstallInfoPath: String;
  InstallPath: String;
  LauncherPath: String;
  AppExePath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 创建安装信息文件（供launcher和updater使用）
    DocsPath := ExpandConstant('{userdocs}\MitaHillFRP');
    ForceDirectories(DocsPath);
    ForceDirectories(DocsPath + '\\Config');
    ForceDirectories(DocsPath + '\\logs');
    
    InstallInfoPath := DocsPath + '\install_info.json';

    // 计算路径（先展开再替换，避免 Pascal 字符串嵌套问题）
    InstallPath := ExpandConstant('{app}');
    StringChange(InstallPath, '\', '/');
    
    LauncherPath := ExpandConstant('{app}') + '\launcher.exe';
    StringChange(LauncherPath, '\', '/');
    
    // 主程序路径变更为 MitaHill-FRP-APP/MinecraftFRP.exe
    AppExePath := ExpandConstant('{app}') + '\MitaHill-FRP-APP\MinecraftFRP.exe';
    StringChange(AppExePath, '\', '/');
    
    InstallInfo := '{' + #13#10 +
      '  "install_path": "' + InstallPath + '",' + #13#10 +
      '  "version": "{#MyAppVersion}",' + #13#10 +
      '  "channel": "{#Channel}",' + #13#10 +
      '  "install_date": "' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') + '",' + #13#10 +
      '  "launcher_path": "' + LauncherPath + '",' + #13#10 +
      '  "app_path": "' + AppExePath + '"' + #13#10 +
      '}';
    
    SaveStringToFile(InstallInfoPath, InstallInfo, False);
  end;
end;

// 卸载前的提示
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox('确定要卸载 MinecraftFRP 吗？' + #13#10#13#10 +
    '您的配置文件将被保留在"文档\MitaHillFRP"目录中。', 
    mbConfirmation, MB_YESNO);
  Result := Response = IDYES;
end;

// 卸载完成
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DocsPath: String;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DocsPath := ExpandConstant('{userdocs}\MitaHillFRP');
    
    if DirExists(DocsPath) then
    begin
      Response := MsgBox('是否同时删除配置文件？' + #13#10#13#10 +
        '配置文件位于: ' + DocsPath, 
        mbConfirmation, MB_YESNO);
      
      if Response = IDYES then
      begin
        DelTree(DocsPath, True, True, True);
      end;
    end;
  end;
end;
