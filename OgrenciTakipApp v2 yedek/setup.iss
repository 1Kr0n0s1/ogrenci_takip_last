[Setup]
AppName=Öğrenci Takip Sistemi
AppVersion=1.0
DefaultDirName={autopf}\OgrenciTakip
DefaultGroupName=OgrenciTakip
OutputBaseFilename=OgrenciTakipKurulum
Compression=lzma
SolidCompression=yes
DisableDirPage=no
SetupIconFile=simge.ico

[Files]
Source: "dist\run.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "simge.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Öğrenci Takip Sistemi"; Filename: "{app}\run.exe"
Name: "{group}\Programı Kaldır"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Öğrenci Takip Sistemi"; Filename: "{app}\run.exe"; IconFilename: "{app}\simge.ico"

[Run]
Filename: "{app}\run.exe"; Description: "Uygulamayı Başlat"; Flags: nowait postinstall skipifsilent