#!/usr/bin/env nu

# Clippy all workspace targets with stricter rules.
def main [] {
    cd ($env.FILE_PWD | path join ..)
    (
        cargo clippy
            --all-targets
            --no-deps
            --workspace
            --
            -D warnings
            -W clippy::explicit_iter_loop
            -W clippy::explicit_into_iter_loop
            -W clippy::semicolon_if_nothing_returned
            -W clippy::doc_markdown
            -W clippy::manual_let_else
    )
    cargo doc --no-deps --workspace --all-features
}
