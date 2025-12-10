; MinecraftFRP Inno Setup 安装脚本
; 替代原来的 src_installer Python安装程序

#define MyAppName "MinecraftFRP"
#define MyAppVersion "0.5.32"
#define MyAppPublisher "MitaHill"
#define MyAppURL "https://github.com/MitaHill/MinecraftFRP"
#define MyAppExeName "launcher.exe"
#define MyAppId "{{8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}"

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

; 输出配置
OutputDir=dist
OutputBaseFilename=MinecraftFRP_Setup_{#MyAppVersion}
SetupIconFile=base\logo.ico

; 压缩配置
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4

; 界面配置
WizardStyle=modern
WizardImageFile=base\logo.bmp
WizardSmallImageFile=base\logo_small.bmp
DisableWelcomePage=no

; 卸载配置
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 权限配置
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 其他配置
ArchitecturesInstallIn64BitMode=x64
AllowNoIcons=yes
ChangesEnvironment=no

; 覆盖更新配置（方案一：支持像微信/Chrome那样的覆盖安装）
CloseApplications=yes            ; 自动检测并提示用户关闭正在运行的程序
RestartApplications=yes          ; 安装完成后自动重启程序（如果之前在运行）
CloseApplicationsFilter=*.exe    ; 需要关闭的程序类型
AllowNetworkDrive=no             ; 不允许安装到网络驱动器

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式:"; Flags: unchecked
Name: "startupicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "快捷方式:"

[Files]
; Launcher (启动器)
Source: "dist\MinecraftFRP_build\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

; 主应用程序目录
Source: "dist\MinecraftFRP_build\app.dist\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

; FRP工具和基础文件
Source: "base\*"; DestDir: "{app}\base"; Flags: ignoreversion recursesubdirs createallsubdirs

; 配置文件
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist

[Dirs]
; 创建日志目录
Name: "{app}\logs"; Permissions: users-modify

; 创建用户文档目录
Name: "{userdocs}\MitaHillFRP"; Permissions: users-modify

[Icons]
; 开始菜单图标
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startupicon

; 桌面图标
Name: "{autodesktop}\Minecraft联机工具"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后可选择立即运行
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
begin
  if CurStep = ssPostInstall then
  begin
    // 创建安装信息文件（供launcher和updater使用）
    DocsPath := ExpandConstant('{userdocs}\MitaHillFRP');
    ForceDirectories(DocsPath);
    
    InstallInfoPath := DocsPath + '\install_info.json';
    
    InstallInfo := '{' + #13#10 +
      '  "install_path": "' + ExpandConstant('{app}') + '",' + #13#10 +
      '  "version": "{#MyAppVersion}",' + #13#10 +
      '  "install_date": "' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') + '",' + #13#10 +
      '  "launcher_path": "' + ExpandConstant('{app}\{#MyAppExeName}') + '",' + #13#10 +
      '  "app_path": "' + ExpandConstant('{app}\app\MinecraftFRP.exe') + '"' + #13#10 +
      '}';
    
    SaveStringToFile(InstallInfoPath, InstallInfo, False);
    
    // 复制默认配置到用户文档目录
    if not FileExists(DocsPath + '\frpc.toml') then
    begin
      FileCopy(ExpandConstant('{app}\config\frpc.toml'), DocsPath + '\frpc.toml', False);
    end;
    
    if not FileExists(DocsPath + '\frp-server-list.json') then
    begin
      FileCopy(ExpandConstant('{app}\config\frp-server-list.json'), DocsPath + '\frp-server-list.json', False);
    end;
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
