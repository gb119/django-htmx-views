@ECHO OFF

pushd %~dp0

if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=sphinx-build
)

%SPHINXBUILD% -M html source build -W --keep-going
popd

