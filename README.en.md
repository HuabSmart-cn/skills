# HuabSmart Skills

> An open repository for organizing and reusing AI capability assets: Skills, Prompts, Agents, MCPs, Workflows, and knowledge files.

- Live directory: [skills.huabsmart.cn](https://skills.huabsmart.cn)
- Source repository: [github.com/HuabSmart-cn/skills](https://github.com/HuabSmart-cn/skills)
- Changelog: [Commits](https://github.com/HuabSmart-cn/skills/commits/main)
- Discussions and reports: [Issues](https://github.com/HuabSmart-cn/skills/issues)

## What this is

Useful AI capabilities are distributed across platforms, communities, and code repositories. HuabSmart Skills organizes publicly shareable assets into a consistent, searchable catalog with metadata, categories, tags, previews, and links to the original files.

This is not a runtime framework and it does not install or execute third-party code for you. The repository stores public metadata and capability files only. The website frontend and deployment implementation are intentionally kept outside this repository.

## Features

- Organize assets by type, platform, domain, and tag
- Provide searchable public metadata for each asset
- Preserve capability descriptions and bundled files
- Keep stable repository paths for each asset
- Make the collection easy for other directories, tools, and applications to consume

## Repository layout

```text
.
├── manifest.json    # Public searchable metadata
└── skills/          # Capability files organized by source and type
```

`manifest.json` describes the public assets and `skills/` contains their files. The website is one consumer of this data; its source code is not part of this repository.

## Contributing

Contributions are welcome: new public assets, metadata corrections, UI improvements, and documentation updates. Before opening a pull request, please verify that:

1. The content may be redistributed and its original license and attribution are respected.
2. No passwords, tokens, private keys, personal information, machine-specific absolute paths, or internal configuration are included.
3. Caches, build artifacts, private data, and unrelated process files are excluded.
4. Scripts, prompts, and external links have received a basic review and relevant risks are documented.

Please use [Issues](https://github.com/HuabSmart-cn/skills/issues) for reports and proposals, or submit a pull request directly.

## Safety and content notice

The repository aims to include only publicly shareable assets. Third-party Skills, Prompts, Agents, and scripts should still be reviewed before use; inclusion does not guarantee their accuracy, security, or suitability. If you find sensitive information or a copyright concern, please report it through Issues.

## Vision

We are collecting the AI capabilities worth preserving from this era. You do not have to start from zero: proven AI paradigms can become your next capability.
