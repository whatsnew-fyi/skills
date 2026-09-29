---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Here's `npm outdated --json` from our app. We don't have time to update everything. What should we actually prioritize?

```json
{
  "next": { "current": "16.2.0", "wanted": "16.3.6", "latest": "16.3.6", "dependent": "acme-web", "location": "node_modules/next" },
  "better-auth": { "current": "1.6.0", "wanted": "1.6.33", "latest": "1.7.6", "dependent": "acme-web", "location": "node_modules/better-auth" },
  "left-pad-nope": { "current": "1.0.0", "wanted": "1.0.0", "latest": "1.0.3", "dependent": "acme-web", "location": "node_modules/left-pad-nope" }
}
```
