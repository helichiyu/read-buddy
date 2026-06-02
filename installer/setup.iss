; Read Buddy 安装程序配置
; 使用 Inno Setup 编译：打开 Inno Setup IDE，打开此文件，点击 Build

[Setup]
AppName=Read Buddy
AppVersion=0.1.0
AppPublisher=Read Buddy
AppPublisherURL=https://github.com/example/read-buddy
DefaultDirName={pf}\Read Buddy
DefaultGroupName=Read Buddy
UninstallDisplayIcon={app}\ReadBuddy.exe
OutputDir=installer_output
OutputBaseFilename=ReadBuddy_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

; 安装界面文字
SetupAppRunningError=安装程序检测到 Read Buddy 正在运行。%n%n请先关闭所有 Read Buddy 窗口，然后点击"重试"继续安装。

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "dist\ReadBuddy\ReadBuddy.exe"; DestDir: "{app}"; Flags: ignoreversion
; 运行时依赖
Source: "dist\ReadBuddy\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; 数据目录（首次安装创建空目录）
Source: "dist\ReadBuddy\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: IsNewInstall

[Icons]
Name: "{group}\Read Buddy"; Filename: "{app}\ReadBuddy.exe"
Name: "{group}\卸载 Read Buddy"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Read Buddy"; Filename: "{app}\ReadBuddy.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ReadBuddy.exe"; Description: "立即运行 Read Buddy"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"

[Code]
function IsNewInstall: Boolean;
begin
  Result := not FileExists(ExpandConstant('{app}\data\readbuddy.db'));
end;
