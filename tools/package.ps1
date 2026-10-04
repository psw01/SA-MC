# Builds both halves of SACraft and packs a release into dist\:
#   SACraft-<version>.zip             the SA mod (install with MO2 or Vortex): the SA-host plugin, its
#                                      ini, and SACraft-Minecraft.zip, the Minecraft it starts
#   SACraft-<version>-pdb.zip         the plugin's debug symbols, for reading crash logs
#   sacraft-fabric-<version>.jar      the Minecraft mod on its own (for your own launcher)
#
# SACraft-Minecraft.zip holds a portable Prism Launcher with a ready "SACraft" instance (Minecraft
# 26.3, Fabric, Fabric API, SACraft). The plugin unpacks it to %LOCALAPPDATA%\SACraft and starts it;
# Prism asks the player to sign in once, then downloads Minecraft and Java itself.
#
#   powershell -ExecutionPolicy Bypass -File tools\package.ps1 [-NoBuild]
param([switch]$NoBuild)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot
$version = (Select-String -Path "$root\fabric\gradle.properties" -Pattern '^version=(.+)$').Matches[0].Groups[1].Value.Trim()

# Pinned downloads (checked against these hashes).
$prismVersion = "11.1.1"
$prismZip = "PrismLauncher-Windows-MSVC-Portable-$prismVersion.zip"
$prismUrl = "https://github.com/PrismLauncher/PrismLauncher/releases/download/$prismVersion/$prismZip"
$prismSha256 = "ab35a770fb06d89d2ccc098079db5db329fb4e68f42b72babd8b095efde3d2d7"
$prismLicenseUrl = "https://raw.githubusercontent.com/PrismLauncher/PrismLauncher/$prismVersion/LICENSE"
$fabricApiJar = "fabric-api-0.161.0+26.3.jar"
$fabricApiUrl = "https://cdn.modrinth.com/data/P7dR8mSH/versions/bNnaTiuM/fabric-api-0.161.0%2B26.3.jar"
$e4mcJar = "e4mc-fabric-6.2.2-modern.jar"
$e4mcUrl = "https://cdn.modrinth.com/data/qANg5Jrr/versions/AouleFRY/e4mc-fabric-6.2.2-modern.jar"
$e4mcSha512 = "01ef0a8c5b76e2cb0effd337bad3350d8807d100d0ec661e01b2ffb20af7b652f756c5eaa11bee233c37905bfd7b573f7a85f3d15bfd2833962c76f02cd59a86"
$fabricApiSha512 = "ed6b2586d6fde11fde8472f5a527c51e99b67026e46f94d4bfd85e7e28ce5ee299173ee16ad576ceb51f39f98d30a811086a6deb1a86a524859cc16e12da109d"

function Get-Pinned([string]$url, [string]$path, [string]$algorithm, [string]$hash) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory (Split-Path $path) -Force | Out-Null
        Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
    }
    if ($hash -and (Get-FileHash $path -Algorithm $algorithm).Hash -ne $hash.ToUpper()) {
        Remove-Item $path
        throw "$path doesn't match its pinned $algorithm hash"
    }
}

# Zip entries named explicitly with forward slashes, as the zip format (and every mod manager)
# expects; Windows PowerShell's own zipping writes backslashes.
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
function New-Zip([string]$path, [System.Collections.IDictionary]$entries) {
    $zip = [System.IO.Compression.ZipFile]::Open($path, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($name in $entries.Keys) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $entries[$name], $name, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        }
    } finally { $zip.Dispose() }
}
function New-ZipFromFolder([string]$path, [string]$folder) {
    $entries = [ordered]@{}
    $base = (Resolve-Path $folder).Path.TrimEnd('\') + '\'
    Get-ChildItem $folder -Recurse -File | Sort-Object FullName | ForEach-Object {
        $entries[$_.FullName.Substring($base.Length).Replace('\', '/')] = $_.FullName
    }
    New-Zip $path $entries
}

if (-not $NoBuild) {
    Push-Location "$root\skse"
    try {
        cmake --preset default | Out-Null
        cmake --build --preset release
        if ($LASTEXITCODE) { throw "the SA-host plugin didn't build" }
    } finally { Pop-Location }
    Push-Location "$root\fabric"
    try {
        .\gradlew.bat build --no-configuration-cache
        if ($LASTEXITCODE) { throw "the Fabric mod didn't build" }
    } finally { Pop-Location }
}

$dll = "$root\skse\build\RelWithDebInfo\SACraft.dll"
$pdb = "$root\skse\build\RelWithDebInfo\SACraft.pdb"
$jar = "$root\fabric\build\libs\sacraft-$version.jar"
foreach ($f in @($dll, $pdb, $jar)) {
    if (-not (Test-Path $f)) { throw "missing $f (build first, or drop -NoBuild)" }
}
$cache = "$root\.tools\prism"
Get-Pinned $prismUrl "$cache\$prismZip" SHA256 $prismSha256
Get-Pinned $fabricApiUrl "$cache\$fabricApiJar" SHA512 $fabricApiSha512
Get-Pinned $e4mcUrl "$cache\$e4mcJar" SHA512 $e4mcSha512
Get-Pinned $prismLicenseUrl "$cache\PrismLauncher-$prismVersion-LICENSE.txt" "" ""

$dist = "$root\dist"
New-Item -ItemType Directory $dist -Force | Out-Null
Get-ChildItem $dist | Remove-Item -Recurse -Force

# The bundled Minecraft: Prism (portable), the SACraft instance, its mods, Prism's default settings.
$bundle = "$dist\bundle"
Copy-Item -Recurse "$root\tools\minecraft-bundle" $bundle
Expand-Archive "$cache\$prismZip" "$bundle\Prism" -Force
Copy-Item "$cache\PrismLauncher-$prismVersion-LICENSE.txt" "$bundle\Prism\LICENSE-PrismLauncher.txt"
(Get-Content "$bundle\Prism\THIRD-PARTY.txt" -Raw).Replace("{PRISM_VERSION}", $prismVersion) | Set-Content "$bundle\Prism\THIRD-PARTY.txt" -NoNewline
$mods = "$bundle\Prism\instances\SACraft\.minecraft\mods"
New-Item -ItemType Directory $mods -Force | Out-Null
Copy-Item "$cache\$fabricApiJar" $mods
Copy-Item "$cache\$e4mcJar" $mods
Copy-Item $jar "$mods\sacraft-$version.jar"
Set-Content "$bundle\bundle-version.txt" "SACraft $version, Prism Launcher $prismVersion, $fabricApiJar, $e4mcJar" -NoNewline
New-ZipFromFolder "$dist\SACraft-Minecraft.zip" $bundle
Remove-Item -Recurse -Force $bundle

New-Zip "$dist\SACraft-$version.zip" ([ordered]@{
    "SA-host/Plugins/SACraft.dll" = $dll
    "SA-host/Plugins/SACraft.ini" = "$root\skse\SACraft.ini"
    "SA-host/Plugins/SACraft/SACraft-Minecraft.zip" = "$dist\SACraft-Minecraft.zip"
    "SA-host/Plugins/SACraft/LICENSE.txt" = "$root\LICENSE"
    "SA-host/Plugins/SACraft/THIRD-PARTY-NOTICES.md" = "$root\THIRD-PARTY-NOTICES.md"
})
New-Zip "$dist\SACraft-$version-pdb.zip" ([ordered]@{ "SACraft.pdb" = $pdb })
Copy-Item $jar "$dist\sacraft-fabric-$version.jar"
Remove-Item "$dist\SACraft-Minecraft.zip"

Get-ChildItem $dist | ForEach-Object { "{0,-40} {1,12:N0} bytes" -f $_.Name, $_.Length }
