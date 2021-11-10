Task default -depends Build

Task Restore {
    Exec { python -m pip install --upgrade build twine }
}

Task Build -depends Restore {
    $readme = $(Get-Childitem "README.md")[0]

    Set-Location src/main
    Write-Output "📦 Build main"

    Copy-Item $readme ./README.md
    Exec { python -m build -o ../../dist }
    Remove-Item ./README.md
    
    Set-Location ../extensions
    foreach ($ext in Get-Childitem -Attributes Directory) {
        Set-Location $ext
        Write-Output "📦 Build $ext" 
        Exec { python -m build -o ../../../dist }
        Set-Location ..
    }
    Set-Location ../..
}

Task Deploy -depends Build {
    Exec { python -m twine upload --skip-existing --repository pypi "dist/*" }
}

Task Install {
    Set-Location ./dist

    Write-Output "🛠 Install dependencies"
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)) {
        Exec { sudo apt-get update >/dev/null }
    }
    elseif ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
        
    }
    elseif ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
        
    }

    Write-Output "🛠 Install main"
    Exec { python -m pip install $(Get-Childitem "aexpy-*.whl")[0] }

    foreach ($ext in Get-Childitem "aexpy_*.whl") {
        Write-Output "🛠 Install $ext"
        Exec { python -m pip install $ext }
    }
    Set-Location ..
}

Task Uninstall {
    Set-Location ./dist
    foreach ($ext in Get-Childitem "aexpy_*.whl") {
        Write-Output "⚒ Uninstall $ext"
        Exec { python -m pip uninstall $ext -y }
    }

    Write-Output "⚒ Uninstall main"
    Exec { python -m pip uninstall $(Get-Childitem "aexpy-*.whl")[0] -y }
    Set-Location ..
}

Task Demo {
    Write-Output "⏳ 1️⃣ Version ⏳"
    Exec { aexpy --version }
    Write-Output "⏳ 2️⃣ Help ⏳"
    Exec { aexpy --help }
    Write-Output "⏳ 3️⃣ Extensions ⏳"
    Exec { aexpy ext }
    Write-Output "⏳ 4️⃣ Demo ⏳"
    Exec { python -m aexpy demo }
    Write-Output "⏳ 5️⃣ Demo in verbose ⏳"
    Exec { aexpy -vvv demo }
    Write-Output "⏳ 6️⃣ Demo from file in preview ⏳"
    Exec { python -m aexpy run ./test/demo.py --preview }
    Write-Output "⏳ 7️⃣ Demo from file ⏳"
    Exec { python -m aexpy run ./test/demo.py }
    Write-Output "⏳ 8️⃣ Demo from file in verbose ⏳"
    Exec { aexpy -vvv run ./test/demo.py }
}

Task Test -depends Unit, Install, Demo, Uninstall

Task Unit {
    python -m test
}

Task RUnit {
    python -m test redo
}

Task Clean {
    foreach ($dist in Get-Childitem ./dist) {
        Write-Output "🗑 Remove $dist"
        Remove-Item $dist
    }
    foreach ($egg in Get-Childitem -Recurse *.egg-info) {
        Write-Output "🗑 Remove $egg"
        Remove-Item -Recurse $egg
    }
}

Task Format {
    Set-Location src/main/aexpy
    autopep8 -r --in-place .

    foreach ($file in Get-Childitem "*.py" -Recurse) {
        isort $file
    }

    Set-Location ../../..
}