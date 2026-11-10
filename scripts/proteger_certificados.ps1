$ErrorActionPreference = 'Stop'
# Restringe únicamente la carpeta privada del proyecto; no modifica almacenes de confianza.
$directorioCertificados = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\certs'))
$identidadCertificados = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
# icacls modifica DACL, sin intentar escribir propietario o auditoría SACL del sistema.
& icacls.exe $directorioCertificados /inheritance:r /grant:r "*${identidadCertificados}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' /q
if ($LASTEXITCODE -ne 0) { throw 'No se pudo restringir la carpeta de certificados.' }
Write-Output 'Carpeta certs restringida al usuario actual y SYSTEM; confianza de Windows sin cambios.'
