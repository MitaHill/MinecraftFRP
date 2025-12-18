; *** Inno Setup version 6.1.0+ Chinese Simplified messages ***
;
; To download user-contributed translations of this file, go to:
;   https://jrsoftware.org/is3rdparty.php
;
; Note: When translating this file, do not translate the strings in the
; "Setup" section.

[LangOptions]
; The following three entries are very important. Be sure to read and 
; understand the '[LangOptions] section' topic in the help file.
LanguageName=Chinese Simplified
LanguageID=$0804
LanguageCodePage=936
; If the language you are translating to requires special font faces or
; sizes, uncomment any of the following entries and change them accordingly.
DialogFontName=Microsoft YaHei UI
DialogFontSize=9
WelcomeFontName=Microsoft YaHei UI
WelcomeFontSize=12
TitleFontName=Microsoft YaHei UI
TitleFontSize=29
CopyrightFontName=Microsoft YaHei UI
CopyrightFontSize=8

[Messages]

; *** Application titles
SetupAppTitle=安装
SetupWindowTitle=安装 - %1
UninstallAppTitle=卸载
UninstallAppFullTitle=%1 卸载

; *** Misc. common
InformationTitle=信息
ConfirmTitle=确认
ErrorTitle=错误

; *** SetupLdr messages
SetupLdrStartupMessage=这将安装 %1。是否继续？
LdrCannotCreateTemp=无法创建临时文件。安装中止
LdrCannotExecTemp=无法执行临时文件。安装中止

; *** Startup error messages
LastErrorMessage=%1.%n%n错误 %2: %3
SetupFileMissing=安装目录中的文件 %1 丢失。请修正此问题或获取新的程序副本。
SetupFileCorrupt=安装文件已损坏。请获取新的程序副本。
SetupFileCorruptOrWrongVer=安装文件已损坏，或是与此版本的安装程序不兼容。请修正此问题或获取新的程序副本。
InvalidParameter=无效的命令行参数: %n%n%1
SetupAlreadyRunning=安装程序正在运行。
WindowsVersionNotSupported=本程序不支持您的 Windows 版本。
WindowsServicePackRequired=本程序需要 %1 Service Pack %2 或更高版本。
NotOnThisPlatform=本程序无法在 %1 上运行。
OnlyOnThisPlatform=本程序必须在 %1 上运行。
OnlyOnTheseArchitectures=本程序只能在以下 Windows 架构版本上安装: %n%n%1
WinVersionTooLowError=本程序需要 %1 %2 或更高版本。
WinVersionTooHighError=本程序无法在 %1 %2 或更高版本上安装。
AdminPrivilegesRequired=在安装本程序之前，您必须以管理员身份登录。
PowerUserPrivilegesRequired=在安装本程序之前，您必须以管理员或有权限的用户身份登录。
SetupAppRunningError=安装程序检测到 %1 当前正在运行。%n%n请先关闭所有它的实例，然后点击“确定”继续，或点击“取消”退出。
UninstallAppRunningError=卸载程序检测到 %1 当前正在运行。%n%n请先关闭所有它的实例，然后点击“确定”继续，或点击“取消”退出。

; *** Startup questions
PrivilegesRequiredOverrideTitle=选择安装模式
PrivilegesRequiredOverrideInstruction=选择安装模式
PrivilegesRequiredOverrideText1=%1 可以为所有用户安装（需要管理员权限），或仅为您安装。
PrivilegesRequiredOverrideText2=%1 可以仅为您安装，或为所有用户安装（需要管理员权限）。
PrivilegesRequiredOverrideAllUsers=为所有用户安装 (&A)
PrivilegesRequiredOverrideAllUsersRecommended=为所有用户安装 (&A) (推荐)
PrivilegesRequiredOverrideCurrentUser=仅为我安装 (&M)
PrivilegesRequiredOverrideCurrentUserRecommended=仅为我安装 (&M) (推荐)

; *** Misc. errors
ErrorCreatingDir=安装程序无法创建目录 "%1"
ErrorTooManyFilesInDir=无法在目录 "%1" 中创建文件，因为里面的文件太多了

; *** Setup common messages
ExitSetupTitle=退出安装
ExitSetupMessage=安装尚未完成。如果您现在退出，程序将不会被安装。%n%n您可以在以后再运行安装程序完成安装。%n%n退出安装吗？
AboutSetupMenuItem=关于安装程序(&A)...
AboutSetupTitle=关于安装程序
AboutSetupMessage=%1 版本 %2%n%3%n%n%1 主页:%n%4
AboutSetupNote=
TranslatorNote=

; *** Buttons
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonOK=确定
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonYesToAll=全是(&A)
ButtonNo=否(&N)
ButtonNoToAll=全否(&O)
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
ButtonWizardBrowse=浏览(&R)...
ButtonNewFolder=新建文件夹(&M)

; *** "Select Language" dialog messages
SelectLanguageTitle=选择安装语言
SelectLanguageLabel=选择安装时要使用的语言。

; *** Common wizard text
ClickNext=点击“下一步”继续，或点击“取消”退出安装。
BeveledLabel=
BrowseDialogTitle=浏览文件夹
BrowseDialogLabel=在下面的列表中选择一个文件夹，然后点击“确定”。
NewFolderName=新文件夹

; *** "Welcome" wizard page
WelcomeLabel1=欢迎使用 [name] 安装向导
WelcomeLabel2=将在您的电脑上安装 [name/ver]。%n%n建议您在继续之前关闭所有其它应用程序。

; *** "Password" wizard page
WizardPassword=密码
PasswordLabel1=本安装程序受密码保护。
PasswordLabel3=请输入密码，密码区分大小写。然后点击“下一步”继续。
PasswordEditLabel=密码(&P):
IncorrectPassword=您输入的密码不正确，请重试。

; *** "License Agreement" wizard page
WizardLicense=许可协议
LicenseLabel=继续安装前请阅读下列重要信息。
LicenseLabel3=请仔细阅读下列许可协议。您在继续安装前必须同意这些协议条款。
LicenseAccepted=我同意此协议(&A)
LicenseNotAccepted=我不同意此协议(&D)

; *** "Information" wizard pages
WizardInfoBefore=信息
InfoBeforeLabel=继续安装前请阅读下列重要信息。
InfoBeforeClickLabel=准备好继续安装后，点击“下一步”。
WizardInfoAfter=信息
InfoAfterLabel=继续安装前请阅读下列重要信息。
InfoAfterClickLabel=准备好继续安装后，点击“下一步”。

; *** "User Information" wizard page
WizardUserInfo=用户信息
UserInfoDesc=请输入您的信息。
UserInfoName=用户名(&U):
UserInfoOrg=组织(&O):
UserInfoSerial=序列号(&S):
UserInfoNameRequired=您必须输入一个名称。

; *** "Select Destination Location" wizard page
WizardSelectDir=选择目标位置
SelectDirDesc=您想将 [name] 安装在哪里？
SelectDirLabel3=安装程序将把 [name] 安装在下列文件夹中。
SelectDirBrowseLabel=点击“下一步”继续。如果您想选择其它文件夹，点击“浏览”。
DiskSpaceMBLabel=至少需要有 [mb] MB 的可用磁盘空间。
CannotInstallToNetworkDrive=安装程序无法安装到网络驱动器。
CannotInstallToUNCPath=安装程序无法安装到 UNC 路径。
InvalidPath=您必须输入包含盘符的完整路径，例如:%n%nC:\APP%n%n或格式为 UNC 的路径:%n%n\\server\share
InvalidDrive=您选择的驱动器或 UNC 共享不存在或不可访问。请选择其它位置。
DiskSpaceWarningTitle=没有足够的磁盘空间
DiskSpaceWarning=安装程序至少需要 [mb] MB 的可用磁盘空间才能安装，但选定的驱动器只有 [mb] MB 的可用空间。%n%n您确定要继续吗？
DirNameTooLong=文件夹名称或路径太长。
InvalidDirName=文件夹名称无效。
BadDirName32=文件夹名称不能包含下列任何字符:%n%n%1
DirExistsTitle=文件夹已存在
DirExists=文件夹:%n%n%1%n%n已经存在。您想在这个文件夹中安装吗？
DirDoesntExistTitle=文件夹不存在
DirDoesntExist=文件夹:%n%n%1%n%n不存在。您想创建该文件夹吗？

; *** "Select Components" wizard page
WizardSelectComponents=选择组件
SelectComponentsDesc=您想安装哪些组件？
SelectComponentsLabel2=勾选您想安装的组件，并取消勾选您不想安装的组件。点击“下一步”继续。
FullInstallation=完全安装
; if possible don't translate 'Compact' as 'Minimal' (I mean 'Minimal' in your language)
CompactInstallation=简洁安装
CustomInstallation=自定义安装
NoUninstallWarningTitle=组件已存在
NoUninstallWarning=安装程序检测到下列组件已安装在您的电脑中:%n%n%1%n%n取消勾选这些组件将不会卸载它们。%n%n您想继续吗？
ComponentSize1=%1 KB
ComponentSize2=%1 MB
ComponentsDiskSpaceMBLabel=当前选择至少需要 [mb] MB 的可用磁盘空间。

; *** "Select Additional Tasks" wizard page
WizardSelectTasks=选择附加任务
SelectTasksDesc=您想执行哪些附加任务？
SelectTasksLabel2=勾选您想在安装 [name] 时执行的附加任务，然后点击“下一步”。

; *** "Select Start Menu Folder" wizard page
WizardSelectProgramGroup=选择开始菜单文件夹
SelectStartMenuFolderDesc=您想在哪里放置程序的快捷方式？
SelectStartMenuFolderLabel3=安装程序将在下列“开始”菜单文件夹中创建程序的快捷方式。
SelectStartMenuFolderBrowseLabel=点击“下一步”继续。如果您想选择其它文件夹，点击“浏览”。
MustEnterGroupName=您必须输入一个文件夹名称。
GroupNameTooLong=文件夹名称或路径太长。
InvalidGroupName=文件夹名称无效。
BadGroupName=文件夹名称不能包含下列任何字符:%n%n%1
NoProgramGroupCheck2=不创建“开始”菜单文件夹(&D)

; *** "Ready to Install" wizard page
WizardReady=准备安装
ReadyLabel1=安装程序现在准备开始在您的电脑上安装 [name]。
ReadyLabel2a=点击“安装”继续，或点击“上一步”检查或更改设置。
ReadyLabel2b=点击“安装”继续。
ReadyMemoUserInfo=用户信息:
ReadyMemoDir=目标位置:
ReadyMemoType=安装类型:
ReadyMemoComponents=选定组件:
ReadyMemoGroup=开始菜单文件夹:
ReadyMemoTasks=附加任务:

; *** "Preparing to Install" wizard page
WizardPreparing=正在准备安装
PreparingDesc=安装程序正在准备在您的电脑上安装 [name]。
PreviousInstallNotCompleted=以前的程序安装/卸载未完成。您需要重启电脑才能完成安装。%n%n重启电脑后，请重新运行安装程序完成 [name] 的安装。
CannotContinue=安装程序无法继续。请点击“取消”退出。
ApplicationsFound=下列应用程序正在使用本安装程序需要更新的文件。建议您允许安装程序自动关闭这些应用程序。
ApplicationsFound2=下列应用程序正在使用本安装程序需要更新的文件。建议您允许安装程序自动关闭这些应用程序。安装完成后，安装程序将尝试重新启动这些应用程序。
CloseApplications=自动关闭应用程序(&A)
DontCloseApplications=不要关闭应用程序(&D)
ErrorCloseApplications=安装程序无法自动关闭所有应用程序。建议您在继续安装之前关闭所有使用本安装程序需要更新的文件的应用程序。

; *** "Installing" wizard page
WizardInstalling=正在安装
InstallingLabel=安装程序正在您的电脑上安装 [name]，请稍候。

; *** "Setup Completed" wizard page
WizardInfoAfter=信息
InfoAfterLabel=安装已完成。
InfoAfterClickLabel=点击“下一步”继续。
WizardFinished=安装完成
FinishedHeadingLabel=[name] 安装向导完成
FinishedLabelNoIcons=安装程序已在您的电脑中安装了 [name]。
FinishedLabel=安装程序已在您的电脑中安装了 [name]。可以通过选择安装的快捷方式运行应用程序。
ClickFinish=点击“完成”退出安装。
FinishedRestartLabel=为了完成 [name] 的安装，安装程序必须重启您的电脑。您想现在重启吗？
FinishedRestartMessage=为了完成 [name] 的安装，安装程序必须重启您的电脑。%n%n您想现在重启吗？
ShowReadmeCheck=是，我想查看自述文件
YesRadio=是，立即重启电脑(&Y)
NoRadio=否，我稍后重启电脑(&N)
; used for example as 'Run MyProg.exe'
RunEntryExec=运行 %1
; used for example as 'View Readme.txt'
RunEntryShellExec=查看 %1

; *** "Setup Needs the Next Disk" stuff
ChangeDiskTitle=安装程序需要下一个磁盘
SelectDiskLabel2=请插入磁盘 %1 并点击“确定”。%n%n如果这个磁盘中的文件可以在其它文件夹中找到，请输入正确的路径或点击“浏览”。
PathLabel=路径(&P):
FileNotInDir2=在 "%2" 中无法定位文件 "%1"。请插入正确的磁盘或选择其它文件夹。
SelectDirectoryLabel=请输入下一个磁盘的位置。

; *** Installation phase messages
SetupAborted=安装未完成。%n%n请修正问题后重新运行安装程序。
AbortRetryIgnoreSelectAction=选择操作
AbortRetryIgnoreRetry=重试(&T)
AbortRetryIgnoreIgnore=忽略错误并继续(&I)
AbortRetryIgnoreCancel=取消安装

; *** Installation status messages
StatusClosingApplications=正在关闭应用程序...
StatusCreateDirs=正在创建目录...
StatusExtractFiles=正在解压文件...
StatusCreateIcons=正在创建快捷方式...
StatusCreateIniEntries=正在创建 INI 条目...
StatusRegisterFiles=正在注册文件...
StatusDeleteFiles=正在删除文件...
StatusRunProgram=正在完成安装...
StatusRestartingApplications=正在重启应用程序...
StatusRollback=正在撤销更改...

; *** Misc. errors
ErrorInternal2=内部错误: %1
ErrorFunctionFailedNoCode=%1 失败
ErrorFunctionFailed=%1 失败; 代码 %2
ErrorMachineType=安装程序无法在您的电脑上运行。
ErrorPluginFilename=无法解压插件 "%1"
ErrorPluginInit=插件初始化失败: %1
ErrorFileInUse=无法打开文件 "%1"，因为正在被其它进程使用。
ErrorAccessDenied=拒绝访问文件 "%1"。
ErrorSourceFileNotFound=源文件 "%1" 不存在
ErrorSourceFileCouldNotBeRead=读取源文件 "%1" 时发生错误
ErrorSourceFileCorrupted=源文件 "%1" 已损坏
ErrorSourceFileCopies=无法在 "%1" 和 "%2" 之间复制文件
ErrorDestinationFileLocked=无法写入文件 "%1"，因为它被 Windows 锁定。
ErrorDestinationFileLockedByApp=无法写入文件 "%1"，因为文件正在被下列应用程序使用:%n%n%2
ErrorDestinationFileNoAccess=无法写入文件 "%1"。
ErrorDestinationFileExists=无法覆盖文件 "%1"。
ErrorPatchTitle=补丁程序错误
ErrorPatch=补丁文件 "%1" 已损坏
ErrorDuplicateFilename=重复的文件名: "%1"
ErrorBindLoad=无法加载库 "%1"
ErrorBindCall=无法找到函数 "%1" (在 "%2" 中)

; *** Setup logging
Logunlink=删除文件: %1
Logcopy=复制文件: %1
Logmove=移动文件: %1 -> %2
Logdelete=删除目录: %1

; *** Uninstall display name markings
; used for example as 'My Program (32-bit)'
UninstallDisplayNameMark=%1 (%2)
; used for example as 'My Program (32-bit, All users)'
UninstallDisplayNameMarks=%1 (%2, %3)
UninstallDisplayNameMark32Bit=32-bit
UninstallDisplayNameMark64Bit=64-bit
UninstallDisplayNameMarkAllUsers=All users
UninstallDisplayNameMarkCurrentUser=Current user

; *** Parameter error messages
ErrorCmdParameter=无效的命令行参数: %1
