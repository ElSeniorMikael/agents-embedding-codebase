#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$InstallDir = $env:AGENT_INDEX_INSTALL_DIR,
    [string]$GlobalBinDir = $env:AGENT_INDEX_GLOBAL_BIN_DIR,
    [switch]$InstallGlobal,
    [switch]$WithOllama,
    [string]$ArchiveUrl = $env:AGENT_INDEX_ARCHIVE_URL
)

$ErrorActionPreference = 'Stop'
if (-not $InstallDir) { $InstallDir = '.agents/embedding-codebase' }
if (-not $GlobalBinDir) { $GlobalBinDir = Join-Path $env:LOCALAPPDATA 'agent-index/bin' }
if (-not $ArchiveUrl) {
    $ArchiveUrl = 'https://github.com/ElSeniorMikael/agents-embedding-codebase/archive/refs/heads/main.zip'
}

# Reuse a supported interpreter, including Python installed through the Windows launcher.
function Find-Python {
    foreach ($candidate in @('python', 'py')) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            $arguments = @()
            if ($candidate -eq 'py') { $arguments = @('-3') }
            & $candidate @arguments -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @{ Command = $candidate; Arguments = $arguments }
            }
        }
    }
    return $null
}

$pythonRuntime = Find-Python
if (-not $pythonRuntime) {
    Write-Host 'Python 3.10+ is required. Installing Python 3.14.7 for the current user...'
    $architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
    switch ($architecture) {
        'ARM64' { $suffix = 'arm64' }
        'AMD64' { $suffix = 'amd64' }
        'x86' { $suffix = '' }
        default { throw "Unsupported Windows architecture: $architecture" }
    }
    $filename = 'python-3.14.7'
    if ($suffix) { $filename += "-$suffix" }
    $filename += '.exe'
    $pythonInstaller = Join-Path ([IO.Path]::GetTempPath()) (([Guid]::NewGuid().ToString()) + '.exe')
    $pythonDir = Join-Path $env:LOCALAPPDATA 'Programs/Python/Python314'
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "https://www.python.org/ftp/python/3.14.7/$filename" -OutFile $pythonInstaller
        $process = Start-Process -FilePath $pythonInstaller -ArgumentList @(
            '/passive', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=0',
            'Include_test=0', ('TargetDir="' + $pythonDir + '"')
        ) -Wait -PassThru
        if ($process.ExitCode -notin @(0, 3010)) { throw "Python installer failed: $($process.ExitCode)" }
    }
    finally { Remove-Item -LiteralPath $pythonInstaller -Force -ErrorAction SilentlyContinue }
    $env:PATH = $pythonDir + ';' + (Join-Path $pythonDir 'Scripts') + ';' + $env:PATH
    $pythonRuntime = Find-Python
    if (-not $pythonRuntime) { throw 'Python 3.10+ is still unavailable after installation. Check PATH and rerun.' }
}
$pythonCommand = $pythonRuntime.Command
$pythonArgs = $pythonRuntime.Arguments

# Prefer the checkout containing this script; downloaded standalone scripts use the archive.
$sourceDir = $PSScriptRoot
$tempDir = $null
try {
    if (-not $sourceDir -or -not (Test-Path -LiteralPath (Join-Path $sourceDir 'src/cli.py'))) {
        $tempDir = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
        New-Item -ItemType Directory -Path $tempDir | Out-Null
        $archive = Join-Path $tempDir 'source.zip'
        Invoke-WebRequest -UseBasicParsing -Uri $ArchiveUrl -OutFile $archive
        Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $tempDir 'source')
        $roots = @(Get-ChildItem -LiteralPath (Join-Path $tempDir 'source') -Directory)
        if ($roots.Count -ne 1) { throw 'Expected one repository directory in the archive.' }
        $sourceDir = $roots[0].FullName
    }
    foreach ($required in @('project_index.py', 'README.md', 'src/cli.py', 'bin/agent-index', 'bin/agent-index.cmd')) {
        if (-not (Test-Path -LiteralPath (Join-Path $sourceDir $required) -PathType Leaf)) {
            throw "Missing runtime file: $required"
        }
    }
    $destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstallDir)
    if ($destination.TrimEnd('\', '/') -eq $sourceDir.TrimEnd('\', '/')) {
        throw 'InstallDir must differ from the source checkout.'
    }
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    $binDir = Join-Path $destination 'bin'
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    foreach ($name in @('project_index.py', 'README.md')) {
        Copy-Item -LiteralPath (Join-Path $sourceDir $name) -Destination $destination -Force
    }
    foreach ($name in @('agent-index', 'agent-index.cmd')) {
        Copy-Item -LiteralPath (Join-Path $sourceDir "bin/$name") -Destination $binDir -Force
    }
    # Replace only runtime source; preserve index caches, configuration, and sibling tools.
    $srcDir = Join-Path $destination 'src'
    if (Test-Path -LiteralPath $srcDir) { Remove-Item -LiteralPath $srcDir -Recurse -Force }
    Copy-Item -LiteralPath (Join-Path $sourceDir 'src') -Destination $srcDir -Recurse
    Get-ChildItem -LiteralPath $srcDir -Directory -Recurse -Filter '__pycache__' |
        Remove-Item -Recurse -Force

    if ($InstallGlobal -or $env:AGENT_INDEX_INSTALL_GLOBAL -eq '1') {
        New-Item -ItemType Directory -Force -Path $GlobalBinDir | Out-Null
        foreach ($name in @('agent-index', 'agent-index.cmd')) {
            Copy-Item -LiteralPath (Join-Path $binDir $name) -Destination $GlobalBinDir -Force
        }
        Write-Host "Installed global dispatcher: $GlobalBinDir"
        Write-Host 'Add that folder to your user PATH to run agent-index from any project subdirectory.'
    }
    Write-Host "Installed agent-index runtime to: $destination"
    Write-Host "Run from the project root: & '$binDir/agent-index.cmd' update"
    if ($WithOllama) {
        if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
            if ($env:OLLAMA_UNINSTALL) { throw 'Unset OLLAMA_UNINSTALL before installing Ollama.' }
            Write-Host 'Installing Ollama using its official installer; complete any permission prompts.'
            $ollamaInstaller = Join-Path ([IO.Path]::GetTempPath()) (([Guid]::NewGuid().ToString()) + '.ps1')
            try {
                Invoke-WebRequest -UseBasicParsing -Uri 'https://ollama.com/install.ps1' -OutFile $ollamaInstaller
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ollamaInstaller
                if ($LASTEXITCODE -ne 0) { throw 'Ollama installation failed.' }
            }
            finally { Remove-Item -LiteralPath $ollamaInstaller -Force -ErrorAction SilentlyContinue }
            $env:PATH = [Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('PATH', 'User') + ';' + $env:PATH
            if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
                throw 'Ollama is not on PATH. Open a new terminal and rerun with -WithOllama.'
            }
        }
        Push-Location -LiteralPath $destination
        try {
            & $pythonCommand @pythonArgs -m src.setup_ollama
            if ($LASTEXITCODE -ne 0) { throw 'Ollama model setup failed.' }
        }
        finally { Pop-Location }
    }
}
finally {
    if ($tempDir -and (Test-Path -LiteralPath $tempDir)) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force
    }
}
