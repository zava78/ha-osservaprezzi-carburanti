$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases' -Headers $headers
foreach ($r in $releases) { Write-Output ("id: $($r.id)  tag: $($r.tag_name)  name: $($r.name)") }
