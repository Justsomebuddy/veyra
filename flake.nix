{
  description = "Veyra — finite observer semantics, recurrence, and proof-ledger experiments";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [
      "aarch64-darwin"
      "aarch64-linux"
      "x86_64-linux"
    ] (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;

        # Runtime and development dependencies mirroring pyproject.toml.
        pythonEnv = python.withPackages (ps: with ps; [
          tqdm
          pytest
          build
        ]);

        checkTools = [ pythonEnv pkgs.ruff pkgs.gnumake pkgs.git ];
        nativeTools = [ pkgs.cargo pkgs.stdenv.cc ];
        suiteTools = checkTools ++ nativeTools;
      in
      {
        devShells = rec {
          python = pkgs.mkShell {
            packages = checkTools ++ [ pkgs.bashInteractive ];
            shellHook = ''
              export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
              export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
              echo "veyra python shell: $(python --version), make, ruff, pytest"
            '';
          };

          lean = pkgs.mkShell {
            packages = [ pkgs.elan ];
            shellHook = ''
              echo "veyra Lean shell: elan available"
              echo "install once: elan toolchain install leanprover/lean4:v4.30.0-rc2"
            '';
          };

          # nixpkgs' cargo wrapper already exposes its matching rustc. The
          # stdenv compiler wrapper supplies the platform linker and SDK.
          native = pkgs.mkShell {
            packages = nativeTools;
            shellHook = ''
              echo "veyra native shell: cargo and rustc available"
            '';
          };

          default = pkgs.mkShell {
            inputsFrom = [ python native ];
          };

          full = pkgs.mkShell {
            inputsFrom = [ default lean ];
          };

          sage = pkgs.mkShell {
            inputsFrom = [ python ];
            packages = [ pkgs.sage ];
          };
        };

        # `nix flake check` runs the platform-independent gates.
        checks.suite = pkgs.runCommandCC "veyra-checks"
          {
            src = self;
            nativeBuildInputs = suiteTools;
          } ''
          cp -r "$src" source && chmod -R u+w source && cd source
          export PYTHONPATH="$PWD"
          export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
          ruff check src tests scripts veyra_sage vam
          python -m pytest -q
          make hygiene
          touch "$out"
        '';
      });
}
