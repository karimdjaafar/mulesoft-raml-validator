# PowerShell completion for raml-validator — how to load it: see INSTALL.md
Register-ArgumentCompleter -Native -CommandName 'raml-validator', 'raml-validator.cmd' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    function Out-Choice([string[]] $values, [string] $tip = '') {
        $values | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $(if ($tip) { $tip } else { $_ }))
        }
    }
    function Out-Path([switch] $DirectoriesOnly) {
        if ($wordToComplete -match '[\\/]$') {
            $dir = $wordToComplete.TrimEnd('\', '/'); $leaf = ''
        } else {
            $dir = Split-Path -Path $wordToComplete -Parent
            $leaf = Split-Path -Path $wordToComplete -Leaf
        }
        $base = if ($dir) { $dir } else { '.' }
        Get-ChildItem -LiteralPath $base -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "$leaf*" -and ($_.PSIsContainer -or (-not $DirectoriesOnly -and $_.Extension -eq '.raml')) } |
            ForEach-Object {
                $text = if ($dir) { Join-Path $dir $_.Name } else { $_.Name }
                if ($_.PSIsContainer) { $text += [IO.Path]::DirectorySeparatorChar }
                [System.Management.Automation.CompletionResult]::new($text, $_.Name, 'ProviderItem', $text)
            }
    }

    $words = @($commandAst.CommandElements | ForEach-Object { $_.ToString() })
    $done = $words.Count
    if ($wordToComplete -ne '') { $done-- }

    $commands = [ordered]@{
        audit      = 'audit a RAML spec (findings + report)'
        fix        = 'corrected RAML + remediation guide'
        run        = 'audit then fix - every deliverable'
        verify     = 'install check and regression suite'
        setup      = 'create .venv with PyYAML and Jinja2'
        completion = 'print the shell completion script'
    }
    if ($done -le 1) {
        $commands.Keys | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $commands[$_])
        }
        Out-Choice @('--version', '--help')
        return
    }

    $command = $words[1]
    $previous = $words[$done - 1]
    if ($previous -eq '--lang') { Out-Choice @('en', 'fr'); return }
    if ($previous -in @('--out-dir', '--root')) { Out-Path -DirectoriesOnly; return }
    if ($previous -eq '--api-description') { return }

    switch ($command) {
        { $_ -in @('audit', 'fix', 'run') } {
            if ($wordToComplete -like '-*') { Out-Choice @('--out-dir', '--lang', '--api-description', '--no-color', '--help') }
            else { Out-Path }
        }
        'verify'     { Out-Choice @('--root', '--help') }
        'completion' { Out-Choice @('zsh', 'bash', 'powershell') }
    }
}
