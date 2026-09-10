{
  "name": "security-scan",
  "version": "0.8.8",
  "displayName": "Qoder Security",
  "description": "Automated security review for Qoder. Pattern-based warnings on edits, cloud-backed diff review on Stop, and agentic commit/push review with SHA tracking. All logic runs in the cross-platform qodersec binary.",
  "author": {
    "name": "CodeSec Team"
  },
  "license": "Apache-2.0",
  "logo": "./assets/logo.svg",
  "keywords": [
    "security",
    "security-review",
    "sast",
    "code-review",
    "vulnerability",
    "diff-review"
  ],
  "category": "Coding",
  "tags": [
    "security",
    "code-review",
    "vulnerability",
    "sast"
  ],
  "hooks": "./.qoder-plugin/qoder-hooks.json",
  "skills": [
    "./skills/security-scan"
  ]
}