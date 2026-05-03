# Add Timestamps To Logs

## Goal

Make CloudCheckin application logs self-identifying by prefixing runtime log messages with a timestamp, so logs remain understandable after NAS, Cookie Cloud, or CloudCheckin restarts.

## Requirements

- Prefix application log messages with local time in the format `YYYY-MM-DD HH:MM:SS (UTC+08:00) message` when `TZ=Asia/Shanghai`.
- Use the configured/local process timezone rather than hard-coding UTC+08:00, so other `TZ` values still produce the correct UTC offset.
- Apply the timestamp prefix consistently to runtime output from scheduler startup, wait status, target startup/success/failure, startup cookie validation, Cookie Cloud diagnostics, and platform check-in modules.
- Avoid relying on Docker's `cloudcheckin |` prefix for time context.
- Preserve existing message content after the timestamp as much as practical.
- Keep tests updated for the new output format.

## Non-Goals

- Do not change check-in scheduling behavior.
- Do not change Cookie Cloud retry behavior.
- Do not change platform check-in request behavior.
