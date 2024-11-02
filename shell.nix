{ pkgs ? import <nixpkgs> {} }:

let
  # Check if zsh is already available in the PATH
    hasZsh = builtins.tryEval (pkgs.runCommand "check-zsh" {} "command -v zsh
    >/dev/null && echo true || echo false") == "true";
in

pkgs.mkShell {
  # Specify dependencies: poetry, python3, and zsh (if not installed)
  buildInputs = [
    pkgs.poetry
    pkgs.python3
  ] ++ (if hasZsh then [] else [ pkgs.zsh ]);

  # Set up the shell hook to use zsh and initiate poetry
  shellHook = ''
    export SHELL=$(command -v zsh || echo "${pkgs.zsh}/bin/zsh")
    ${pkgs.poetry}/bin/poetry env use ${pkgs.python3}/bin/python
    source $(${pkgs.poetry}/bin/poetry env info --path)/bin/activate
    ${pkgs.poetry}/bin/poetry install
  '';
}

