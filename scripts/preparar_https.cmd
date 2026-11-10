@echo off
setlocal
pushd "%~dp0.."
docker build --target runtime -t el-sobre-de-las-ocho-app:etapa1 .
if errorlevel 1 goto fallo
if not exist certs mkdir certs
docker run --rm --user 0 --read-only --network none --tmpfs /tmp --mount "type=bind,source=%CD%\certs,target=/certificados" el-sobre-de-las-ocho-app:etapa1 python -m app.certificates generar
if errorlevel 1 goto fallo
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\proteger_certificados.ps1
if errorlevel 1 goto fallo
docker compose up -d --build --wait --wait-timeout 120
if errorlevel 1 goto fallo
echo HTTPS preparado: https://127.0.0.1:8443/acceso
echo La confianza de la CA requiere una accion explicita del usuario. Consulte docs\SEGURIDAD_RED.md.
popd
exit /b 0
:fallo
echo No se completo HTTPS. No se habilito una alternativa HTTP de autenticacion.
popd
exit /b 1
