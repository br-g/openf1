{
  description = "Flake based development environment for openf1 project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Check if zsh is already available in the PATH
        hasZsh = builtins.tryEval (pkgs.runCommand "check-zsh" {} "command -v zsh
        >/dev/null && echo true || echo false") == "true";
      in {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          poetry
          python3
          mongodb
          mongodb-tools
        ] ++ (if hasZsh then [] else [ pkgs.zsh ]);

        shellHook = ''
          export SHELL=$(command -v zsh || echo "${pkgs.zsh}/bin/zsh")
          ${pkgs.poetry}/bin/poetry env use ${pkgs.python3}/bin/python
          source $(${pkgs.poetry}/bin/poetry env info --path)/bin/activate
          ${pkgs.poetry}/bin/poetry install
        '';
      };
    }
  );
}

#let
#  # Check if zsh is already available in the PATH
#  hasZsh = builtins.tryEval (pkgs.runCommand "check-zsh" {} "command -v zsh
#  >/dev/null && echo true || echo false") == "true";
#in
#
#pkgs.mkShell {
#  # Specify dependencies: poetry, python3, and zsh (if not installed)
#  buildInputs = with pkgs; [
#    poetry
#    python3
#
#    # MongoDB server
#    mongodb
#    mongodb-tools
#  ] ++ (if hasZsh then [] else [ pkgs.zsh ]);
#
#  # Set up the shell hook to use zsh and initiate poetry
#  shellHook = ''
#    export SHELL=$(command -v zsh || echo "${pkgs.zsh}/bin/zsh")
#    ${pkgs.poetry}/bin/poetry env use ${pkgs.python3}/bin/python
#    source $(${pkgs.poetry}/bin/poetry env info --path)/bin/activate
#    ${pkgs.poetry}/bin/poetry install
#  '';
#}
#
