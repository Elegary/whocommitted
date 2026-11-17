# Regenerate with: vhs docs/demo.tape  (from the repository root)
Output docs/demo.gif

Require uv
Require jq

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 720
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms

Env PS1 "$ "
Env BASH_SILENCE_DEPRECATION_WARNING "1"

Hide
Type "uv sync -q && export PATH=$PWD/.venv/bin:$PATH && clear"
Enter
Sleep 2s
Show

Type "whocommitted extract octocat/Hello-World"
Sleep 300ms
Enter
Sleep 4s

Type "whocommitted extract psf/requests --group-by kind --sort commits -f txt | grep '^#'"
Sleep 300ms
Enter
Sleep 5s

Type "whocommitted extract octocat/Hello-World -f json --sort commits | jq '.[0]'"
Sleep 300ms
Enter
Sleep 5s
