; Read Buddy 安装程序配置
; 使用 Inno Setup 编译：打开 Inno Setup IDE，打开此文件，点击 Build

[Setup]
AppName=Read Buddy
AppVersion=0.1.0
AppPublisher=Read Buddy
AppPublisherURL=https://github.com/example/read-buddy
DefaultDirName={commonpf}\Read Buddy
DefaultGroupName=Read Buddy
UninstallDisplayIcon={app}\ReadBuddy.exe
OutputDir=installer_output
OutputBaseFilename=ReadBuddy_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "..\dist\ReadBuddy\ReadBuddy.exe"; DestDir: "{app}"; Flags: ignoreversion
; 运行时依赖
Source: "..\dist\ReadBuddy\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

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
