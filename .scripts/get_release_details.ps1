$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$rid = 275508658
$release = Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Headers $headers
Write-Output "id: $($release.id)"
Write-Output "tag_name: $($release.tag_name)"
Write-Output "name: $($release.name)"
Write-Output "draft: $($release.draft)"
Write-Output "published_at: $($release.published_at)"
Write-Output "body:\n$($release.body)"
