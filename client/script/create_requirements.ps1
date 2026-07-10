uv pip freeze | Out-File ./data/requirements.bin -Encoding utf8

$requirementsPath = "./data/requirements.bin"
$requirementsForLinuxPath = "./data/requirements_for_posix.bin"
$patterns = "^pywin32", "^pyWinhook", "^win32_setctime"

(Get-Content -Path $requirementsPath) | Where-Object {
    -not ($_ -match ($patterns -join "|"))
} | Set-Content -Path $requirementsForLinuxPath -Encoding utf8
