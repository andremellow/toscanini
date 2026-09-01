# Power Dev Workflow Command Center

This optional local dashboard visualizes the workflow without replacing Codex's native agent UI.

The page starts in clearly labeled demo mode. A production bridge should translate documented Codex App Server notifications into this event contract. Hooks may supplement lifecycle and tool events. Never parse transcript files as a stable API or expose prompts, hidden reasoning, secrets, environment values, or raw tool output.

```json
{"timestamp":"2026-08-31T14:32:18Z","threadId":"thr_example","parentThreadId":"thr_parent","agentId":"worker","agentType":"worker","event":"handoff","state":"working","from":"orchestrator","to":"worker","summary":"Begin bounded implementation","artifact":"specs/024/architecture.md"}
```

Use Node.js 22.13 or newer, then run `npm run dev` or `npm run build`.
