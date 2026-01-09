if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN non è impostato. Imposta l'ambiente e riprova."
    exit 1
}

$tag = 'v0.1.5'
try {
    Write-Output "Creazione tag $tag..."
    git tag -a $tag -m "Release $tag"
    Write-Output "Pushing tag $tag to origin..."
    git push origin $tag
}
catch {
    Write-Error "Errore git: $_"
    exit 2
}

$body = @{
    tag_name   = $tag
    name       = $tag
    body       = "Release ${tag}: aggiornamenti minori, aggiunto link al sito del Ministero per ricerca ID stazioni."
    draft      = $false
    prerelease = $false
} | ConvertTo-Json

try {
    Write-Output "Creazione release su GitHub API..."
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases" -Method Post -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' } -Body $body -ContentType 'application/json'
    Write-Output "Release creata: $($response.html_url)"
}
catch {
    Write-Error "Errore durante la creazione della release: $_"
    exit 3
}
