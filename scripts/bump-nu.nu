#!/usr/bin/env nu

# Update Nushell dependencies and README version badge to a specified version.
def main [
    version?: string  # Nushell version, e.g. `0.116.1`.
] {
    cd ($env.FILE_PWD | path join ..)
    if $version == null {
        nu $env.CURRENT_FILE --help
    } else {
        let result = (
            cargo add
                $"nu-cmd-lang@($version)"
                $"nu-parser@($version)"
                $"nu-protocol@($version)"
                $"nu-utils@($version)"
                $"nuon@($version)"
            | complete
        )
        if $result.stdout != "" { print --no-newline $result.stdout }
        if $result.stderr != "" { print --stderr --no-newline $result.stderr }
        if $result.exit_code != 0 {
            error make --unspanned { msg: "failed to update Nushell dependencies" }
        }
        let input_string = 'https://img.shields.io/badge/nushell-v\d+\.\d+\.\d+-green'
        let output_string = $"https://img.shields.io/badge/nushell-v($version)-green"
        open --raw README.md
        | str replace --regex $input_string $output_string
        | save --force README.md
    }
}
