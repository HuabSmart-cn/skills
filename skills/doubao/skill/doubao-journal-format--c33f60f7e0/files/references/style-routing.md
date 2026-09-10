# Style Spec And Routing

Read this before generating or consuming `style_spec.json`, classifying roles, applying text rules, installing role styles, or cleaning direct formatting.

## Intermediate Style Spec

The role style spec is the mandatory bridge between template extraction and target formatting. It must be generated from the template only, then consumed by the target stage. Target styles, target style names, and target direct formatting must never influence what a role should look like.

All source formats must enter this same bridge. Do not maintain separate target-formatting routes for native `.docx`, legacy `.doc`, PDF, images, or website rules after evidence extraction. Convert every usable source into a role-based `style_spec.json`, then classify the target into `role_map.json`, then apply the spec. The only difference between source formats is evidence priority and confidence.

When `references/template-distill-render-qa.md` is used, `template_evidence.json` or `qa_report.json` may support `style_spec.json` only on the template side. Target-before QA can warn about direct-format cleanup needs and object-preservation risks, but it must not define the desired role style. The target file answers "where is each role"; the template evidence answers "how each role should look."

Source-aware priority is locked:

- Native `.docx`/`.dotx`: `user_rules > template_text_rules > representative_template_direct_format > template_style_xml > property-level granular fallback only for explicit prose text rules with missing/default core properties`. Do not inject whole-role bundled fallback into clean native DOCX styles because missing properties can be intentional Word inheritance. Instruction-heavy native DOCX templates are different: if text says `摘要：楷体小5号` or `文章正文是5号宋体` but the paragraph/style exposes no real line spacing, indentation, or paragraph spacing, preserve the explicit font/字号 and fill only the missing paragraph properties from granular fallback.
- All non-DOCX sources, including legacy `.doc`/`.dot`, PDF, screenshot/image/OCR, website, and externally supplied visual rules: `user_rules > extracted_text_rules > source_column_detection_for_fallback_variant > bundled_OOXML_fallback > legacy_dictionary_fallback`. For website links, the source-column step is allowed only when website/user text explicitly says single-column or double-column manuscript layout; otherwise choose single-column fallback and record `website_unspecified_columns_default_single`.

Priority wording is important: "non-DOCX source is lower confidence" means the carrier lacks reliable Word XML style parts. It does not mean extracted text rules are weaker than fallback. Explicit text rules must lock the exact property channels they mention, and fallback may only fill unstated or unsafe-default channels. Re-apply explicit user/text rules after fallback merge.

Rules JSON explicit fields do not need `source` or `confidence` to be honored. A role rule containing deterministic formatting keys such as `size`, `font_size`, `fonts`, `font`, `spacing`, `line_spacing`, `indent`, `paragraph.indentation`, `align`, `bold`, `italic`, `color`, `tabs`, or `numbering` is an explicit text/user rule by structure and must survive non-DOCX sanitization. Drop only fields marked as visual/geometry inference, such as `source=visual_role_alignment`, `pdf_visual`, `visual_supplement`, or similar visual-only evidence.

Rules JSON must be normalized before any visual sanitization, text-rule merge, fallback merge, or style installation. Accept both the flat schema and OOXML-summary schema:

```json
{
  "roles": {
    "body": {
      "size": "24",
      "spacing": {"line": "480", "lineRule": "auto"}
    }
  }
}
```

```json
{
  "body": {
    "summary": {
      "pPr": {"spacing": {"line": "480"}},
      "rPr": {"sz": {"val": "24"}}
    }
  }
}
```

The second form must normalize to `body.size="24"` and `body.spacing={"line":"480","lineRule":"auto"}`. `summary.pPr.ind`, `summary.pPr.jc`, `summary.rPr.rFonts`, root-level `pPr/rPr`, and `paragraph.pPr` are also valid sources for the same flat fields. Record accepted summary paths in `rules_schema_diagnostics.normalized_fields`. Invalid role names or role rules with no recognized deterministic fields must generate schema warnings; do not silently run fallback as if the user rule succeeded.

Spacing normalization is mandatory, not cosmetic. WordprocessingML `w:spacing/@w:line` is not a free-form decimal field. Convert semantic line-spacing rules before writing XML: `1.5`/`1.5x`/`一倍半` -> `360` with `lineRule="auto"`, `double-spaced`/`double line spacing` -> `480`, `single-spaced`/`single line` -> `240`, and exact point spacing -> points*20 with `lineRule="exact"`. This applies to flat rules, OOXML-summary rules, extracted website/PDF text, legacy DOC text, `style_spec.json`, role `style_xml`, `pPr_xml`, `Normal`, `docDefaults`, and any final direct paragraph spacing. If a reused spec already contains `w:line="1.5"`, repair it before repack and record the repair in QA.

Website author guidelines are not native Word templates. Pages such as Nature formatting guides often state submission rules such as `Contributions should be double-spaced and written in English`, organization order, title length, reference limits, and figure/table placement, but not full Word style XML. Treat these as high-priority extracted text rules for the properties they state; map manuscript-wide rules to content roles such as abstract/summary, body, reference items, captions, and display equations. Missing typography, paragraph spacing, table XML, equation tabs, and page setup still come from the selected standard fallback. Do not infer Nature/Science production PDF layout or double columns from the website brand when the manuscript guide does not explicitly require it.

When the source is non-DOCX or a blank carrier DOCX used only because the formatter requires a package, the carrier template must be treated as unformatted. Start generated role styles from a clean style shell and write only properties from explicit text/user rules plus granular fallback. Do not inherit blank-template, converted DOC/DOT, PDF, website, OCR, or Word built-in Heading/Reference colors, underlines, borders, small caps, theme colors, stale sizes, single line spacing `w:line="240"`, style links, support files, headers/footers, or page XML. Visual/geometry evidence may only provide reliable `fallback_columns`, except website links where visual/brand/page-layout evidence must not provide double-column fallback without explicit website/user text.

Blank/carrier templates must materialize fallback instead of preserving Word defaults:

- If the source package has no meaningful format text/sample content but external rules exist, route it as `blank_carrier_template`.
- Generate `docDefaults` and `Normal` from the body fallback baseline, not from the blank Word package.
- Generate every role style from explicit text/user rules plus granular fallback. A blank carrier's existing `Normal`, `Heading1`, `Heading2`, and `Bibliography` styles are containers only.
- Validate at least `title`, `heading1`, `body`, and `equation` role styles after spec creation. For Chinese fallback, `title` and `heading1` must have explicit `w:spacing w:before="240" w:after="120" w:line="360" w:lineRule="auto"` where defined by fallback, `body` must have `w:line="360"`, and `Normal/docDefaults` must not remain at blank-template `w:line="240"` when the fallback language is Chinese.
- If user rules explicitly set body spacing, such as `line="480"`, materialize that same locked spacing into weak-source `docDefaults` and `Normal` after fallback merge. Do not leave `Normal` at `w:line="240"` while `9body` has `w:line="480"`, because unbound/body-like paragraphs can display with Normal spacing.
- When reusing an old `style_spec.json` created from a blank carrier, repair it before installation by rebuilding low-confidence role styles from the current fallback. Do not let stale `style_xml` carry the old carrier's 240-line spacing back into QA repair.

When the format source began as legacy `.doc` or `.dot` and was converted to temporary `.docx`, the converted package is only a text-extraction carrier. Do not use converted `styles.xml`, `Normal`, `Heading`, bibliography styles, representative paragraph/run direct formatting, rendered visual crosscheck, settings/fontTable/theme, headers/footers, or page XML as style authority. If converted text rules such as `正文五号宋体` are found, they lock only the stated properties; missing properties come from fallback. If the converted/rendered source reliably exposes single-column or double-column layout, record only `fallback_columns` for variant selection and final risk notes.

Legacy `.doc`/`.dot`, PDF, screenshot/image/OCR, website, and plain text rules must use the same bridge. Extract text rules and optional column-count metadata only; after that, the target formatting stage is still role-map plus style-spec application. Do not let a converted `Normal`, `Heading`, bibliography style, blank carrier, website display stylesheet, or PDF/OCR visual sample define blue headings, red underlined references, exact colors, exact fonts, underlines, local emphasis, role alignment, spacing, indentation, tabs, or other default shell formatting.

For converted `.doc`/`.dot`, do not hardcode `fallback_columns=1`. Although converted OpenXML is not style authority, the converted `sectPr/w:cols` count is allowed low-confidence structural evidence for choosing `zh_single`, `zh_double`, `en_single`, or `en_double`. If the converted package has any section with `w:cols/@w:num >= 2`, choose double-column fallback unless explicit user/rules metadata says otherwise. If `sectPr` detection fails, use source filename keywords such as `双栏`, `单栏`, `two-column`, or `single-column` as lower-priority hints, then default to single-column with a warning.

For non-DOCX sources, never replace an entire role with fallback just because one property is missing. Merge at property level. A rule like `正文宋体五号` locks body font and size; missing line spacing must come from fallback, not coarse visual evidence or converted-DOC direct formatting. A short rule paragraph can provide font/size wording but must not donate its paragraph spacing, indentation, tabs, color, or border.

If a website guideline says `正文 12 pt Times New Roman` and says nothing about spacing, body font/size must be `12 pt Times New Roman`; spacing may come from fallback. Do not report this as the text rule being weaker than fallback.

Apply the same property-level merge to native DOCX instruction templates. A native `.docx` is not automatically a high-quality style authority when it is mostly explanatory prose or sample instructions. If role text rules are explicit but the matched paragraph is a format hint, a label plus writing instructions, or has default/placeholder paragraph XML such as `w:spacing w:line="0"`, treat its paragraph properties as missing and complete them from granular fallback. Do not use this as permission to overwrite a clean native DOCX style that has trustworthy paragraph XML.

For paired abstract/keyword rules, allow font and字号 to propagate between the pair when one side gives the explicit format and the other side is only a keyword-count/example sentence. For example, `摘要：楷体小5号` plus `关键词：3-8个关键词...` means both abstract and keywords use 楷体小五 unless a stronger rule says otherwise; paragraph spacing/indent still comes from explicit evidence or fallback at property level.

Low-confidence visual evidence is column-count only. For PDF, converted DOC/DOT preview, OCR/image visual hints, screenshots, and blank carriers, do not emit or trust visual role, alignment, `size`, `bold`, `indent`, `spacing`, tabs, colors, underlines, or run-level properties. For website links, do not infer column count from visual hints, publisher brands, production article pages, or common journal practice; use explicit website/user text or default to single-column. Explicit prose/user text rules still win; everything else must come from fallback.

If visual/geometry screening can reliably determine single-column or double-column layout, write only `_meta.fallback_columns`/`source_column_detection`. Long front-matter lines are often misread as justified, so non-DOCX visual-only alignment must be dropped rather than normalized into `center`.

For weak-source fallback, abstract and keyword content should default to five-point size (`w:sz=21`). The labels `摘要`, `关键词`, `Abstract`, and `Key words`/`Keywords` are run-level bold markers only; the following abstract/keyword content must remain non-bold. Recognize label variants including `[Abstract]`, `【Abstract】`, `ABSTRACT`, `[摘要]`, `[Keywords]`, and `KEY WORDS` with or without a colon. Do not encode whole-style bold on `abstract`, `keywords`, `english_abstract`, or `english_keywords` just to bold the label.

Apply this same restriction to all non-DOCX visual routes, not only PDF. If image/OCR/website/rendered-preview rules JSON contains role alignment, `size`, `fonts`, `bold`, `italic`, `color`, `underline`, `indent`, `spacing`, `tabs`, or similar visual-format fields, sanitize them before merging with template text rules. Only explicit user/prose rules may keep style fields.

For clean publisher templates with explicit Word styles, canonical `styleId` mapping is mandatory and overrides heuristic paragraph guessing:

| Role | Preferred template style IDs |
|---|---|
| `title` | `IOPTitle`, `Titledocument`, `TitleDocument`, `Title` |
| `author` | `Authors`, `Author` |
| `affiliation` | `Affiliation`, `AdressLines`, `AddressLines`, `Affiliations` |
| `abstract` | `Abstract` |
| `keywords` | `KeyWords`, `Keywords`, `Keyword`, `KeyWord` |
| `heading1` | `IOPH1`, then `Head1`, then `Heading1` |
| `heading2` | `IOPH2`, then `Head2`, then `Heading2` |
| `heading3` | `IOPH3`, then `Head3`, then `Heading3` |
| `body` | `Para`, then `BodyText` variants, then `Normal` |
| `figure_caption` | `FigureCaption`, `CaptionFigure`, then `Caption` |
| `table_caption` | `TableCaption`, `CaptionTable`, `TableTitle`, then `Caption` |
| `references_heading` | `ReferenceHead`, `ACMRefHead`, then `Heading1` |
| `reference_item` | `IOPRefs`, `Bibentry`, `BibEntry`, `References`, `Bibliography` |
| `equation` | `DisplayFormula`, `Equation`, `Formula` |
| `english_title` | `EnglishTitle`, `TitleEnglish` |
| `english_author` | `EnglishAuthors`, `AuthorsEnglish` |
| `english_affiliation` | `EnglishAffiliation`, `AffiliationEnglish` |
| `english_abstract` | `EnglishAbstract`, `AbstractEnglish` |
| `english_keywords` | `EnglishKeywords`, `KeywordsEnglish` |
| `metadata` | `Metadata` |
| `citation_format` | `CitationFormat` |

Heuristics may fill missing roles only after this canonical pass, but canonical styles must be usage-validated. A style that merely exists in `styles.xml` is only a candidate; it is authoritative only when real template paragraphs for that role actually use that `pStyle`, or when the role is a publisher-defined non-body role with no better paragraph evidence. ACM, IOP, and other publisher templates often keep visible body/head/reference formatting in custom style IDs such as `Para`, `Head1`, `IOPH1`, `FigureCaption`, `ReferenceHead`, `IOPRefs`, and `Bibentry`; these must beat generic Word defaults such as `Normal`, `Heading1`, and `Heading2`. If a normal body paragraph has no explicit `pStyle`, build the role from `docDefaults + Normal` plus that paragraph's direct `pPr/rPr`; never emit an empty body fallback.

For unknown journal templates, do not rely only on the fixed canonical table. Also inspect every template style's `styleId`, visible `w:name`, real paragraph usage, and expanded `basedOn` chain. Generic semantic style names such as `ArticleTitle`, `PaperTitle`, `ManuscriptTitle`, `HeadingLevel1`, `SectionHead2`, `FigCaption`, `TableCaption`, `BibliographyEntry`, `ReferenceItem`, or `Refs` may define the role even when the style ID is not in the known-publisher list. This semantic fallback must run before content-only paragraph guessing, but it must avoid collisions: `TableTitle/FigureTitle` are captions, `ReferenceHead` is the references heading, and `Subtitle/RunningTitle/ShortTitle` are not the main title.

Each role entry must include:

- role id and generated `style_id`, such as `title -> 1title`, `body -> 9body`;
- display name and style type;
- structured font summary: CJK/Latin/complex fonts, size, bold/italic, color, underline, emphasis mark, strike, superscript/subscript, hidden text, character spacing, position, scaling, kerning, shading, border, language;
- structured paragraph summary: alignment, outline level, text direction, indentation, first-line/hanging indent, spacing before/after, line spacing, grid flags, keep/page-break controls, widow control, tabs, numbering, borders, shading, frame, text alignment;
- locked text rule that overrode template XML, if any;
- source sample and source style id for audit;
- raw `pPr_xml`, `rPr_xml`, and full `style_xml`.

When a canonical `styleId` is selected, the audit sample/signature must come from a real template paragraph using that same `pStyle` whenever possible. Do not borrow samples from another detected paragraph of the same role, and do not use table style-inventory rows as role samples. Publisher-specific canonical IDs such as IOP `IOPTitle`, `IOPH1`, `IOPH2`, `IOPH3`, and `IOPRefs` must be treated as explicit role evidence before generic Word styles; record the selected `source_style_id` and its `basedOn` chain in `style_spec.json`.

Run-level direct formatting must be promoted to role styles only through representative coverage, never by the first formatted run:

- Paragraph-level `pPr/rPr` is authoritative for paragraph mark character style. If it exists, use it before inspecting child runs.
- If paragraph-level `pPr/rPr` is absent, infer representative run formatting by text-length coverage across all meaningful text runs. Font, size, language, and character spacing may be promoted only when the same property covers a strong majority of the paragraph text.
- Local emphasis properties such as italic, bold, underline, color, highlight, shading, superscript/subscript, strike, emphasis marks, hidden text, caps, and character position need an even stronger near-whole-paragraph majority before promotion.
- A single formatted run, or the first formatted run, is not representative when surrounding text has no matching direct formatting. This prevents reference examples, captions, metadata, and body paragraphs from turning entirely italic/bold/colored because one journal name, volume number, marker, or hint phrase is formatted locally.
- Run-level superscript markers remain a separate marker pass. They must not become whole-paragraph `style/rPr` or nested `style/pPr/rPr`.

Few-shot:

| Template evidence | Expected behavior |
|---|---|
| Reference item text has normal authors/year, italic journal name, bold volume, then normal pages | `reference_item` keeps the paragraph/font/size evidence but does not write whole-style italic or bold. |
| Figure caption has only `Fig. 1` bold and the caption text normal | `figure_caption` does not become entirely bold. |
| A full title paragraph is entirely bold/italic in nearly every run | The emphasis may be promoted because it is representative whole-role formatting. |
| Author line has superscript affiliation numbers after names | Do not promote `vertAlign=superscript` to `author`; apply superscript only to detected marker runs later. |

Role-source content consistency is mandatory and must be generic, not a publisher-specific blacklist:

- A paragraph can define a core role style only when its text, position, and surrounding context are compatible with that role. Being early in the template, short, large, bold, or assigned a custom Word style is insufficient.
- Publisher metadata, date/DOI/copyright/received/revised/accepted notes, footnotes, correspondence notes, UI/operation instructions, and placeholder/rule prose must not become the source sample for `title`, `author`, `affiliation`, `abstract`, `keywords`, `body`, headings, captions, or references.
- Such paragraphs may map to `metadata` only when they are real front-matter metadata; footnotes and operation/help text should usually be skipped as style sources unless the target has an explicit matching role.
- If a style's first used paragraph is metadata/instruction text, do not infer the style's semantic role from position alone. Continue scanning for a content-consistent paragraph using the same role, or fall back through the source-aware priority chain.
- Do not fix this with hardcoded style-name blacklists. Use content features such as date/DOI/copyright/received/revised/accepted markers, footnote/correspondence language, UI operation words, formatting-rule wording, and role-zone context.

Few-shot:

| Template evidence | Expected behavior |
|---|---|
| Early paragraph says `Date of publication...` and uses a custom style | Treat as metadata/source-noise, not title/body, even if it is the first visible paragraph. |
| Early paragraph says `Digital Object Identifier...` or contains `doi:10...` | Do not use it as author/body/title style evidence; at most map as metadata. |
| A footnote/copyright/correspondence note appears before the real paper title | Skip it as a core role source; keep scanning for the real title/author/body samples. |
| A custom style's first used paragraph is a Word operation instruction such as Alt Text guidance | Do not use that paragraph's `pPr/rPr` as the body or caption style. |
| Real paper title appears after several publisher metadata rows | The real title paragraph, not the first visible short paragraph, supplies `title` evidence. |

Body source selection has an extra guardrail:

- Do not select `BodyText`, `BodyTextIndent`, `Para`, or any body canonical style just because it exists in `styles.xml`.
- First verify that actual body-like template paragraphs use that `pStyle`.
- If the template has many real body paragraphs with `pStyle=None`, use their `Normal/docDefaults + direct paragraph/run formatting` as the body style source even when an unused `BodyText` style exists.
- Record this as `source_route=detected_paragraph`, not `used_canonical_style_id`.
- This avoids Springer-style templates where headings/captions use named custom styles but real body text remains Normal, while an unused `BodyText` style in `styles.xml` has different font/size/spacing.
- When a real body paragraph has no explicit `pStyle`, materialize the template default paragraph style, usually `Normal`, together with `docDefaults` before applying the paragraph's direct formatting. Do not treat `pStyle=None` as `docDefaults` only; otherwise properties stored on `Normal`, such as `w:jc w:val="both"`, disappear.
- Do not use a hard minimum text length such as 80 characters to decide whether a body source is trustworthy. Short placeholder body samples such as `Enter text here.`, `Sample body text.`, or a short real paragraph may still carry the correct `Normal`/`BodyText` formatting.
- Keep the false-positive guard: short formatting hints and operation instructions are not body formatting samples. Text such as `正文宋体五号`, `文章正文是5号宋体`, `right-click ... Edit Alt Text`, `Use single tab stops...`, or other Word operation/help text must not contribute paragraph `jc`, `spacing`, `ind`, or tab settings to the body style.
- Before inheriting body paragraph spacing from a detected source paragraph, decide whether the source paragraph is a real body sample or only a format hint. A paragraph like `文章正文是5号宋体` can provide font/size text rules, but its paragraph spacing is not trustworthy.
- If a real body sample has explicit spacing such as `line="300" lineRule="auto"` or exact fixed spacing, preserve it. If the source has `line="0"` or no spacing, treat line spacing as unspecified and use the granular fallback.

Generated style IDs must use this readable sequence:

| Role | Generated style ID |
|---|---|
| `title` | `1title` |
| `author` | `2author` |
| `affiliation` | `3affiliation` |
| `abstract` | `4abstract` |
| `keywords` | `5keywords` |
| `heading1` | `6heading1` |
| `heading2` | `7heading2` |
| `heading3` | `8heading3` |
| `body` | `9body` |
| `figure_caption` | `10figurecaption` |
| `table_caption` | `11tablecaption` |
| `references_heading` | `12referencesheading` |
| `reference_item` | `13referenceitem` |
| `equation` | `14equation` |
| `english_title` | `15englishtitle` |
| `english_author` | `16englishauthor` |
| `english_affiliation` | `17englishaffiliation` |
| `english_abstract` | `18englishabstract` |
| `english_keywords` | `19englishkeywords` |
| `metadata` | `20metadata` |
| `citation_format` | `21citationformat` |

The raw XML fields are authoritative. The structured fields are for audit, model routing, and sanity checks. If the structured parser misses a Word featur

... [Content truncated, total 48,908 chars] ...