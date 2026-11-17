# Regenerate with: vhs docs/demo.tape  (from the repository root)
Output docs/demo.gif

Require uv
Require jq

Set Shell "bash"
Set FontSize 16
Set Width 1300
Set Height 560
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set WaitTimeout 60s
Set WaitPattern /\$\s*$/

Env PS1 "$ "
Env BASH_SILENCE_DEPRECATION_WARNING "1"

Hide
Type "uv sync -q && export PATH=$PWD/.venv/bin:$PATH && clear"
Enter
Wait
Show

# 1. Top contributors of a project
Type "# Who built Flask? Top contributors, bots and noreply addresses excluded"
Enter
Type "whocommitted extract pallets/flask --sort commits --no-bots --no-noreply --limit 10 --redact"
Enter
Wait
Sleep 4s
Ctrl+L

# 2. Who is still active
Type "# Who maintains requests today? Most recent activity first"
Enter
Type "whocommitted extract psf/requests --sort last-seen --no-bots --no-noreply --limit 8 --redact"
Enter
Wait
Sleep 4s
Ctrl+L

# 3. Any git host + company filter
Type "# Any git host: which GitLab employees work on the GitLab CLI?"
Enter
Type "whocommitted extract https://gitlab.com/gitlab-org/cli -d gitlab.com --no-bots --no-noreply -s commits -n 8 --redact"
Enter
Wait
Sleep 4s
Ctrl+L

# 4. Scripting
Type "# Script it: plain emails for your pipelines, CSV for spreadsheets"
Enter
Type `whocommitted extract pallets/click -f json --sort commits --no-noreply --limit 5 --redact | jq -r '.[].email'`
Enter
Wait
Sleep 1s
Type "whocommitted extract pallets/click -f csv --redact -o click.csv"
Enter
Wait
Sleep 5s

Hide
Type "rm -f click.csv"
Enter
