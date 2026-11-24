{
  description = "The Nushell Formatter";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      perSystem = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowDeprecatedx86_64Darwin = true;
          };
          # nufmt requires Rust 1.98.1 or newer. nixos-26.05 defaults to Rust 1.95.
          rust = pkgs.rustPackages_1_98;
          nufmt = rust.rustPlatform.buildRustPackage {
            name = "nufmt";
            src = ./.;
            cargoLock.lockFile = ./Cargo.lock;

            meta = {
              description = "A formatter for Nushell scripts, built entirely on Nushell's own parsing infrastructure";
              homepage = "https://github.com/nushell/nufmt";
              license = pkgs.lib.licenses.mit;
              mainProgram = "nufmt";
            };
          };
        in
        {
          packages = {
            default = nufmt;
            inherit nufmt;
          };

          devShells.default = pkgs.mkShell {
            inputsFrom = [ nufmt ];
            packages = [
              pkgs.nushell
              pkgs.rust-analyzer
              rust.rustfmt
              rust.clippy
            ];
          };

          formatter = pkgs.nixfmt-tree;
        }
      );
    in
    {
      packages = builtins.mapAttrs (_: outputs: outputs.packages) perSystem;
      devShells = builtins.mapAttrs (_: outputs: outputs.devShells) perSystem;
      formatter = builtins.mapAttrs (_: outputs: outputs.formatter) perSystem;
    };
}
