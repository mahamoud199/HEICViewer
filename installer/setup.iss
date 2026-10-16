; Inno Setup Script for HEIC Viewer
; Compiler: Inno Setup 6 (ISCC.exe)

#define MyAppName "HEIC Viewer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mahmoud"
#define MyAppExeName "HEICViewer.exe"

[Setup]
AppId={{E68A91D2-8C8B-4BF4-9A47-1B89ACDE3A89}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\installer_output
OutputBaseFilename=HEICViewer-Setup
SetupIconFile=..\assets\app.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "associate_heic"; Description: "ربط وتعيين ملفات .heic و .heif لفتحها تلقائياً بهذا البرنامج"; GroupDescription: "ارتباطات الملفات (File Associations):"

[Files]
Source: "..\..\dist\HEICViewer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Registry]
; 1. تسجيل امتداد .heic
Root: HKCR; Subkey: ".heic"; ValueType: string; ValueName: ""; ValueData: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heic"; ValueType: string; ValueName: "Content Type"; ValueData: "image/heic"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heic"; ValueType: string; ValueName: "PerceivedType"; ValueData: "image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heic\OpenWithProgids"; ValueType: none; ValueName: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic

; 2. تسجيل امتداد .heif
Root: HKCR; Subkey: ".heif"; ValueType: string; ValueName: ""; ValueData: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heif"; ValueType: string; ValueName: "Content Type"; ValueData: "image/heif"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heif"; ValueType: string; ValueName: "PerceivedType"; ValueData: "image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heif\OpenWithProgids"; ValueType: none; ValueName: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic

; 3. تسجيل معرف البرنامج HEICViewer.Image
Root: HKCR; Subkey: "HEICViewer.Image"; ValueType: string; ValueName: ""; ValueData: "HEIC Image File"; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCR; Subkey: "HEICViewer.Image\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCR; Subkey: "HEICViewer.Image\shell\open"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCR; Subkey: "HEICViewer.Image\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associate_heic

; 4. تسجيل في قائمة التطبيقات المدعومة Applications
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".heic"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: "Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".heif"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate_heic

; 5. تسجيل في مستكشف ويندوز الحالي (HKCU)
Root: HKCU; Subkey: "Software\Classes\.heic"; ValueType: string; ValueName: ""; ValueData: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCU; Subkey: "Software\Classes\.heif"; ValueType: string; ValueName: ""; ValueData: "HEICViewer.Image"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCU; Subkey: "Software\Classes\HEICViewer.Image\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associate_heic

; 6. تسجيل مشغلات المعاينة المصغرة ShellEx Thumbnails
Root: HKCR; Subkey: ".heic\ShellEx\{{e357fccd-a995-4576-b01f-234630154e96}}"; ValueType: string; ValueName: ""; ValueData: "{{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}}"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: ".heic\ShellEx\{{BB2E617C-0920-11d1-9A0B-00C04FC2D6C1}}"; ValueType: string; ValueName: ""; ValueData: "{{3F30C968-480A-4C6C-862D-EFC0897BB84B}}"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCR; Subkey: "HEICViewer.Image\ShellEx\{{e357fccd-a995-4576-b01f-234630154e96}}"; ValueType: string; ValueName: ""; ValueData: "{{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}}"; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCU; Subkey: "Software\Classes\HEICViewer.Image\ShellEx\{{e357fccd-a995-4576-b01f-234630154e96}}"; ValueType: string; ValueName: ""; ValueData: "{{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}}"; Flags: uninsdeletekey; Tasks: associate_heic
Root: HKCU; Subkey: "Software\Classes\.heic\ShellEx\{{e357fccd-a995-4576-b01f-234630154e96}}"; ValueType: string; ValueName: ""; ValueData: "{{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}}"; Flags: uninsdeletevalue; Tasks: associate_heic
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.heic\ShellEx\{{e357fccd-a995-4576-b01f-234630154e96}}"; ValueType: string; ValueName: ""; ValueData: "{{C7657C4A-9F68-40fa-A4DF-96BC08EB3551}}"; Flags: uninsdeletevalue; Tasks: associate_heic

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

