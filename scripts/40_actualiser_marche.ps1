# Lance l'actualisation quotidienne du tableau de bord (cours, indicateurs, actualites, site).
# Appele par la tache planifiee Windows "Cacao - actualisation du tableau de bord".
# Sortie de chaque execution : data/live/derniere_execution.txt ; historique : data/live/journal.csv
$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine
$env:PYTHONPATH = "src"
& "$racine\.venv\Scripts\python.exe" -u "$racine\scripts\40_actualiser_marche.py" *> "$racine\data\live\derniere_execution.txt"
exit $LASTEXITCODE
