$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$preCommitPath = ".git/hooks/pre-commit"
$preCommitContent = @'
#!/bin/sh
set -e
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check-lf.ps1 -Fix
git update-index --again
'@

[System.IO.File]::WriteAllText($preCommitPath, $preCommitContent.Replace("`r`n", "`n"), $utf8NoBom)
Write-Host "Installed pre-commit hook to $preCommitPath"

$commitMsgPath = ".git/hooks/commit-msg"
$commitMsgContent = @'
#!/bin/sh
set -e
subject=$(head -n 1 "$1" | tr -d '\r\n')
len=${#subject}
if [ "$len" -gt 50 ]; then
    echo "Error: Commit subject line is $len characters (max 50):" >&2
    echo "  $subject" >&2
    exit 1
fi
'@

[System.IO.File]::WriteAllText($commitMsgPath, $commitMsgContent.Replace("`r`n", "`n"), $utf8NoBom)
Write-Host "Installed commit-msg hook to $commitMsgPath"
