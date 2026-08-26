# Demo recording for the README. Regenerate with:
#   vhs demo/howl.tape
# Requires: brew install vhs
#
# Run from the repository root -- howl reads its cache from ./.cache/

Output demo/howl.gif

Set Shell zsh
Set FontSize 15
Set Width 1500
Set Height 800
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 60ms

# The repo build, not whatever version is installed globally -- the
# published 0.2.2 still prints the mixed-language header this demo exists
# to show fixed.
Hide
Type "export PATH=$PWD/.venv/bin:$PATH" Enter
Type "clear" Enter
Sleep 1s
Show

# Two different lenses on the same library, so the demo shows the tool
# doing something -- not the same rows twice.
Type "howl --top 6"
Sleep 600ms
Enter
Sleep 5s

Type "howl --sort hidden-gems --top 5"
Sleep 600ms
Enter
Sleep 6s
