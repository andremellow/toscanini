# Troubleshooting

- Run `scripts/inspect-project --target <repo>` to review detection without writing.
- Run `scripts/doctor --target <repo>` to find drift or missing installed files.
- Use `--dry-run` before install and update operations.
- Resolve reported conflicts manually; the installer never overwrites an unmanaged file.
- Review the Git diff to roll back generated changes. No automatic deletion is performed.
- If the command center says **Demo telemetry**, it is using representative events. Connect a supported App Server bridge or emit the documented JSON event contract before relying on it as live evidence.
