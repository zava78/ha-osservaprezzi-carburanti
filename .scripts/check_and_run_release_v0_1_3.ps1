if ($env:GITHUB_TOKEN) {
    Write-Output 'GITHUB_TOKEN=SET'
    Write-Output '--- Eseguo lo script create_release_v0_1_3.ps1 ---'
    & .\scripts\create_release_v0_1_3.ps1
}
else {
    Write-Output 'GITHUB_TOKEN=NOT SET'
}
