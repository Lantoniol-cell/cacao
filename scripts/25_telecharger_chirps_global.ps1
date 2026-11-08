# Telecharge le fichier mondial CHIRPS v2.0 mensuel (7,7 Go) avec reprise apres coupure.
# Usage : powershell -File scripts/25_telecharger_chirps_global.ps1
$url = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/netcdf/chirps-v2.0.monthly.nc"
$cible = "data\raw\t2_climat\chirps_global\chirps-v2.0.monthly.nc"
$taille = 7755032602

for ($i = 1; $i -le 2000; $i++) {
    if ((Test-Path $cible) -and (Get-Item $cible).Length -ge $taille) { break }
    curl.exe -s -S -L -C - --connect-timeout 30 --speed-limit 1000 --speed-time 120 -o $cible $url
    $recu = if (Test-Path $cible) { (Get-Item $cible).Length } else { 0 }
    Write-Output ("essai {0} : {1:N2} Go, {2}" -f $i, ($recu / 1GB), (Get-Date -Format "HH:mm:ss"))
    if ($recu -lt $taille) { Start-Sleep -Seconds 20 }
}
$recu = if (Test-Path $cible) { (Get-Item $cible).Length } else { 0 }
if ($recu -ne $taille) { Write-Output "Taille finale inattendue : $recu au lieu de $taille"; exit 1 }
Write-Output "Termine : $recu octets"
