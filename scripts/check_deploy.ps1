$urls = @(
  'https://n8n-ai-saas-ei9o-fov8pu1ur-rx-services-solutions.vercel.app',
  'https://n8n-ai-saas-ei9o-fov8pu1ur-rx-services-solutions.vercel.app/demo',
  'https://n8n-ai-saas-ei9o-fov8pu1ur-rx-services-solutions.vercel.app/api/demo/formulas'
)
foreach ($u in $urls) {
  try {
    $r = Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 30
    Write-Output "URL: $u"
    Write-Output "Status: $($r.StatusCode)"
    if ($u -like '*api*') {
      $body = $r.Content
      if ($body.Length -gt 1000) { $body = $body.Substring(0,1000) }
      Write-Output "Body snippet:\n$body"
    }
    Write-Output "----"
  } catch {
    Write-Output "URL: $u"
    Write-Output "ERROR: $($_.Exception.Message)"
    Write-Output "----"
  }
}
