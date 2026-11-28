# Ecosystem defaults

Use this table only to fill a `gap` in the gate matrix. A tool the repo already configures always wins over the default here. When a cell lists alternatives, prefer the one whose config or dependency already exists in the repo. Use the first one only when neither exists.

| Ecosystem | Detect | Format | Lint / static analysis | Typecheck / compile | Fast tests |
|---|---|---|---|---|---|
| JavaScript / TypeScript | `package.json` | Prettier, or Biome | ESLint, or Biome | `tsc --noEmit` | the `test` script |
| Python | `pyproject.toml`, `setup.py`, `requirements*.txt` | `ruff format` (keep Black if configured) | `ruff check` | mypy or pyright, if configured | `pytest -x -q` |
| Go | `go.mod` | `gofmt` / `goimports` | `golangci-lint run` (minimum: `go vet ./...`) | `go build ./...` | `go test -short ./...` |
| Rust | `Cargo.toml` | `cargo fmt` | `cargo clippy --all-targets -- -D warnings` | `cargo check` | `cargo test` |
| Java | `pom.xml`, `build.gradle(.kts)` | Spotless with google-java-format | Checkstyle, PMD, SpotBugs, or Error Prone | `mvn -q compile` / `./gradlew compileJava` | `mvn test` / `./gradlew test` |
| Kotlin / Android | `build.gradle(.kts)` with a Kotlin plugin | ktlint or ktfmt (through Spotless) | detekt; Android: `./gradlew lint` (slow, pre-push) | `./gradlew compileKotlin` | `./gradlew test` |
| Scala | `build.sbt` | scalafmt | scalafix | `sbt compile` | `sbt test` |
| C / C++ | `CMakeLists.txt`, `meson.build`, `Makefile`, `*.c`/`*.cpp` | clang-format | clang-tidy (needs `compile_commands.json`), cppcheck | the repo's build (`cmake --build build`) | `ctest --test-dir build` |
| C# / .NET | `*.sln`, `*.csproj` | `dotnet format whitespace` / `style` | `dotnet format analyzers`, Roslyn analyzers | `dotnet build` | `dotnet test` |
| Swift | `Package.swift`, `*.xcodeproj` | swift-format or SwiftFormat | SwiftLint | `swift build` | `swift test` |
| Ruby | `Gemfile` | RuboCop `-a`, or standardrb | RuboCop | Sorbet, if configured | `rspec` / `rake test` |
| PHP | `composer.json` | PHP-CS-Fixer, or Laravel Pint | PHPStan or Psalm | — | PHPUnit or Pest |
| Dart / Flutter | `pubspec.yaml` | `dart format` | `dart analyze` / `flutter analyze` | covered by analyze | `dart test` / `flutter test` |
| Elixir | `mix.exs` | `mix format` | Credo | `mix compile --warnings-as-errors` | `mix test` |
| Shell | `*.sh`, scripts with a shell shebang | shfmt | ShellCheck | — | bats, if present |
| Terraform | `*.tf` | `terraform fmt` | tflint | `terraform validate` | — |
| Docker | `Dockerfile` | — | hadolint | — | — |
| Markdown / YAML / JSON | `*.md`, `*.yml`, `*.json` | Prettier, if the repo has Node | markdownlint, yamllint | — | — |

## Cross-cutting hygiene

These checks apply to every repo, whatever its languages. With the pre-commit framework, take them from `pre-commit/pre-commit-hooks` and `gitleaks/gitleaks`. With other managers, wire the equivalent commands.

- Trailing whitespace and missing final newline.
- Merge-conflict markers.
- Large files added by mistake.
- Filename case conflicts.
- YAML, JSON, and TOML syntax.
- Secret scanning with gitleaks.
