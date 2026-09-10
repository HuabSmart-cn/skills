# Report Contract

## Internal source report

Create `report-source.md` before the DOCX. It is the canonical content and evaluation sidecar, not the user-facing deliverable. It must contain:

- title, audience, date, scope, and important assumptions;
- an executive answer that directly addresses the question;
- substantive sections tailored to the task rather than a fixed essay template;
- citations attached to every material sourced claim;
- explicit uncertainty, limitations, and unresolved disagreements;
- recommendations or implications only when requested or clearly useful;
- a claim-to-source ledger with source title, publisher/author, date, URL, and access notes.

Keep native tool citation syntax in this sidecar so automated evaluators can trace sources. Do not expose the ledger or sidecar in the final handoff unless the user asks for working files.

## DOCX structure

Use `$documents` and choose the lightest structure that serves the reader. A typical report contains:

1. Title block with report date and scope.
2. Executive answer or key findings.
3. Analysis organized around the user's real questions.
4. Implications, options, or recommendations when relevant.
5. Uncertainties and limitations.

Do not force a methodology section, source table, or appendix when it adds no reader value. Do not package ordinary prose into dense tables.

Default to the Documents skill's `standard_business_brief` preset for executive research and `narrative_proposal` for longer narrative work, unless the user supplies a template or requests another visual system.

## Citations in Word

- Convert source citations into human-readable Word footnotes or endnotes.
- Include source title, publisher or author, publication/update date when available, and clickable URL.
- Place the note marker immediately after the supported claim.
- Reuse a source consistently and avoid redundant notes on the same sentence.
- Do not expose internal search IDs, tool call IDs, or evaluation markers.
- Add a bibliography only when requested or required by the chosen professional format.

Follow the Documents skill's footnote/endnote guidance and accessibility requirements.

## Artifact QA

The DOCX is mandatory. Before delivery:

- audit headings, lists, tables, footnotes, hyperlinks, page geometry, headers/footers, and direct-formatting drift;
- render the DOCX to page PNGs with the Documents workflow;
- inspect every page at 100% zoom for clipping, overlap, awkward breaks, broken tables, missing glyphs, and citation defects;
- revise and re-render until clean;
- if LibreOffice is unavailable, complete the structural-QA fallback and state that visual review was not completed.

## Handoff

Return a concise high-level summary and a link to the final `.docx`. Link no QA images, temporary files, source ledger, or Markdown sidecar unless the user asks for them.
