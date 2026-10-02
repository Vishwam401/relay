# scripts/seal_audit.ps1 -- audit every tracked *_PREDICTIONS_FROZEN.md against its committed blob (P-57).
# Read-only by default. With -Restore it rewrites a working copy from the index ONLY when that copy differs from
# the committed bytes by line endings alone; any other difference is reported as BLOCKED and left untouched.
# Usage: pwsh -File scripts\seal_audit.ps1 -Out logs\<name>.txt [-Restore]
param([Parameter(Mandatory = $true)][string]$Out, [switch]$Restore)
function Sha([byte[]]$b) { [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($b)) }
function LfOnly([byte[]]$b) {
  $o = [System.Collections.Generic.List[byte]]::new($b.Length)
  for ($i = 0; $i -lt $b.Length; $i++) { if (-not ($b[$i] -eq 13 -and $i + 1 -lt $b.Length -and $b[$i + 1] -eq 10)) { $o.Add($b[$i]) } }
  return , $o.ToArray()
}
function CommittedSha([string]$f) {
  $tmp = New-TemporaryFile
  cmd /c "git cat-file blob HEAD:$f > `"$($tmp.FullName)`""
  $h = Sha ([IO.File]::ReadAllBytes($tmp.FullName)); Remove-Item $tmp; return $h
}
$r = [System.Collections.Generic.List[string]]::new()
$seals = @(git ls-files -- '*_PREDICTIONS_FROZEN.md')
$restored = 0; $blocked = 0
foreach ($f in $seals) {
  $committed = CommittedSha $f
  $bytes = [IO.File]::ReadAllBytes((Resolve-Path $f))
  $wc = Sha $bytes; $lf = Sha (LfOnly $bytes)
  $eol = ((git ls-files --eol -- $f) -split '\s+')[1]
  $action = '-'
  if ($Restore -and $wc -ne $committed) {
    if ($lf -eq $committed) { Remove-Item $f; git checkout -- $f; $restored++; $action = 'restored' }
    else { $blocked++; $action = 'BLOCKED_content_differs' }
  }
  $r.Add($f + ' ' + $eol + ' wc=' + $wc.Substring(0, 8) + ' lf_only=' + $lf.Substring(0, 8) + ' committed=' + $committed.Substring(0, 8) + ' action=' + $action)
}
$match = 0; $blobMatch = 0
foreach ($f in $seals) {
  if ((CommittedSha $f) -eq (Sha ([IO.File]::ReadAllBytes((Resolve-Path $f))))) { $match++ }
  if ((git hash-object $f) -eq (git rev-parse "HEAD:$f")) { $blobMatch++ }
}
$r.Add('seals=' + $seals.Count + ' wc_sha_equals_committed=' + $match + ' hash_object_equals_head=' + $blobMatch + ' restored=' + $restored + ' blocked=' + $blocked)
$r.Add('attr_line2=' + (Get-Content .gitattributes | Select-Object -Skip 1 -First 1))
$r.Add('git_status_lines=' + @(git status --porcelain).Count)
$r | Out-File -Encoding utf8 $Out
Get-Content $Out
