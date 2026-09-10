{
  "name": "latex",
  "version": "0.2.6",
  "interface": {
    "logoDark": "./assets/latex.png",
    "logo": "./assets/latex.png",
    "displayName": "LaTeX",
    "shortDescription": "Compile LaTeX with TeX tools",
    "longDescription": "LaTeX workflows for Codex that use bundled Tectonic first for simple projects, fall back to detected TeX Live or MacTeX for fuller projects, validate local LaTeX readiness, and optionally install a Codex-managed full TeX Live runtime only when no usable system installation is present.",
    "developerName": "OpenAI",
    "category": "Education & Research",
    "capabilities": [
      "Interactive",
      "Read",
      "Write"
    ],
    "websiteURL": "https://openai.com/",
    "privacyPolicyURL": "https://openai.com/policies/row-privacy-policy/",
    "termsOfServiceURL": "https://openai.com/policies/row-terms-of-use/",
    "defaultPrompt": [
      "Use latex-doctor to check whether this machine can compile LaTeX.",
      "Use latex-compile to build the main TeX file in this project, trying Tectonic first when the project is simple.",
      "Use texlive-runtime-installer to install managed full TeX Live only if no existing TeX Live is detected."
    ],
    "brandColor": "#2563EB",
    "screenshots": []
  },
  "description": "Compile LaTeX with bundled Tectonic for simple projects and TeX Live or MacTeX for full projects.",
  "author": {
    "name": "OpenAI"
  },
  "homepage": "https://github.com/openai/openai/tree/master/plugins/latex",
  "repository": "https://github.com/openai/openai/tree/master/plugins/latex",
  "license": "Proprietary",
  "keywords": [
    "latex",
    "tectonic",
    "texlive",
    "mactex",
    "latexmk",
    "pdf",
    "typesetting"
  ],
  "skills": "./skills/"
}