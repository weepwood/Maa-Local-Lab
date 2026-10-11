Unicode true
!include "MUI2.nsh"

Name "Maa Local Lab (MXU)"
OutFile "..\release\Maa-Local-Lab-MXU-setup-win-x64.exe"
InstallDir "$LOCALAPPDATA\Programs\Maa Local Lab"
RequestExecutionLevel user
ShowInstDetails show
ShowUninstDetails show

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "安装" SEC_MAIN
    SetOutPath "$INSTDIR"
    File /r "..\release\portable\*"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\Maa Local Lab.lnk" "$INSTDIR\Maa Local Lab.exe"
SectionEnd

Section "Uninstall"
    Delete "$SMPROGRAMS\Maa Local Lab.lnk"
    Delete "$INSTDIR\Maa Local Lab.exe"
    RMDir /r "$INSTDIR\maafw"
    RMDir /r "$INSTDIR\resource"
    RMDir /r "$INSTDIR\tools"
    RMDir /r "$INSTDIR\licenses"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\Uninstall.exe"
    ; 保留 config / debug / cache 等用户数据，避免静默删除。
    RMDir "$INSTDIR"
SectionEnd
