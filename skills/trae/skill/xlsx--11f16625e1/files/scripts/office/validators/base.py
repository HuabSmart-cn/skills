"""
Base validator with common validation logic for document files.
"""

import re
from pathlib import Path

import defusedxml.minidom
import lxml.etree


class BaseSchemaValidator:
    """Base validator with common validation logic for document files."""

    # Validation errors to ignore (patterns that appear in error messages)
    # These are XSD schema errors that don't affect document functionality,
    # typically caused by specific editors like LibreOffice.
    IGNORED_VALIDATION_ERRORS = [
        # LibreOffice writes hyphenationZone in wrong order in word/settings.xml.
        # The XSD requires strict element ordering, but LibreOffice puts doNotHyphenateCaps
        # before hyphenationZone. This doesn't affect document rendering.
        "hyphenationZone",
    ]

    # Elements whose 'id' attributes must be unique within their file
    # Format: element_name -> (attribute_name, scope)
    # scope can be 'file' (unique within file) or 'global' (unique across all files)
    UNIQUE_ID_REQUIREMENTS = {
        # Word elements
        "comment": ("id", "file"),  # Comment IDs in comments.xml
        "commentrangestart": ("id", "file"),  # Must match comment IDs
        "commentrangeend": ("id", "file"),  # Must match comment IDs
        "bookmarkstart": ("id", "file"),  # Bookmark start IDs
        "bookmarkend": ("id", "file"),  # Bookmark end IDs
        # Note: ins and del (track changes) can share IDs when part of same revision
        # PowerPoint elements
        "sldid": ("id", "file"),  # Slide IDs in presentation.xml
        "sldmasterid": ("id", "global"),  # Slide master IDs must be globally unique
        "sldlayoutid": ("id", "global"),  # Slide layout IDs must be globally unique
        "cm": ("authorid", "file"),  # Comment author IDs
        # Excel elements
        "sheet": ("sheetid", "file"),  # Sheet IDs in workbook.xml
        "definedname": ("id", "file"),  # Named range IDs
        # Drawing/Shape elements (all formats)
        "cxnsp": ("id", "file"),  # Connection shape IDs
        "sp": ("id", "file"),  # Shape IDs
        "pic": ("id", "file"),  # Picture IDs
        "grpsp": ("id", "file"),  # Group shape IDs
    }

    # Container elements where ID uniqueness checks should be skipped
    # These hold references that intentionally duplicate IDs of elements they reference
    # Example: <p14:sldId id="301"> in sectionLst references <p:sldId id="301"> in sldIdLst
    EXCLUDED_ID_CONTAINERS = {
        "sectionlst",  # PowerPoint sections - sldId elements reference slides by ID
    }

    # Mapping of element names to expected relationship types
    # Subclasses should override this with format-specific mappings
    ELEMENT_RELATIONSHIP_TYPES = {}

    # Unified schema mappings for all Office document types
    SCHEMA_MAPPINGS = {
        # Document type specific schemas
        "word": "ISO-IEC29500-4_2016/wml.xsd",  # Word documents
        "ppt": "ISO-IEC29500-4_2016/pml.xsd",  # PowerPoint presentations
        "xl": "ISO-IEC29500-4_2016/sml.xsd",  # Excel spreadsheets
        # Common file types
        "[Content_Types].xml": "ecma/fouth-edition/opc-contentTypes.xsd",
        "app.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesExtended.xsd",
        "core.xml": "ecma/fouth-edition/opc-coreProperties.xsd",
        "custom.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesCustom.xsd",
        ".rels": "ecma/fouth-edition/opc-relationships.xsd",
        # Word-specific files
        "people.xml": "microsoft/wml-2012.xsd",
        "commentsIds.xml": "microsoft/wml-cid-2016.xsd",
        "commentsExtensible.xml": "microsoft/wml-cex-2018.xsd",
        "commentsExtended.xml": "microsoft/wml-2012.xsd",
        # Chart files (common across document types)
        "chart": "ISO-IEC29500-4_2016/dml-chart.xsd",
        # Theme files (common across document types)
        "theme": "ISO-IEC29500-4_2016/dml-main.xsd",
        # Drawing and media files
        "drawing": "ISO-IEC29500-4_2016/dml-main.xsd",
    }

    # Unified namespace constants
    MC_NAMESPACE = "http://schemas.openxmlformats.org/markup-compatibility/2006"
    XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

    # Common OOXML namespaces used across validators
    PACKAGE_RELATIONSHIPS_NAMESPACE = (
        "http://schemas.openxmlformats.org/package/2006/relationships"
    )
    OFFICE_RELATIONSHIPS_NAMESPACE = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    )
    CONTENT_TYPES_NAMESPACE = (
        "http://schemas.openxmlformats.org/package/2006/content-types"
    )

    # Folders where we should clean ignorable namespaces
    MAIN_CONTENT_FOLDERS = {"word", "ppt", "xl"}

    # All allowed OOXML namespaces (superset of all document types)
    OOXML_NAMESPACES = {
        "http://schemas.openxmlformats.org/officeDocument/2006/math",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
        "http://schemas.openxmlformats.org/drawingml/2006/main",
        "http://schemas.openxmlformats.org/drawingml/2006/chart",
        "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
        "http://schemas.openxmlformats.org/drawingml/2006/diagram",
        "http://schemas.openxmlformats.org/drawingml/2006/picture",
        "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://schemas.openxmlformats.org/presentationml/2006/main",
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
        "http://www.w3.org/XML/1998/namespace",
    }

    def __init__(self, unpacked_dir, original_file, verbose=False):
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file)
        self.verbose = verbose

        # Set schemas directory
        self.schemas_dir = Path(__file__).parent.parent / "schemas"

        # Get all XML and .rels files
        patterns = ["*.xml", "*.rels"]
        self.xml_files = [
            f for pattern in patterns for f in self.unpacked_dir.rglob(pattern)
        ]

        if not self.xml_files:
            print(f"Warning: No XML files found in {self.unpacked_dir}")

    def validate(self):
        """Run all validation checks and return True if all pass."""
        raise NotImplementedError("Subclasses must implement the validate method")

    def repair(self) -> int:
        """Run auto-repairs. Returns count of repairs made. Subclasses should override and call super()."""
        return self.repair_whitespace_preservation()

    def repair_whitespace_preservation(self) -> int:
        """Add xml:space='preserve' to w:t/a:t elements with leading/trailing whitespace."""
        repairs = 0

        for xml_file in self.xml_files:
            try:
                content = xml_file.read_text(encoding="utf-8")
                dom = defusedxml.minidom.parseString(content)
                modified = False

                for elem in dom.getElementsByTagName("*"):
                    if elem.tagName.endswith(":t") and elem.firstChild:
                        text = elem.firstChild.nodeValue
                        if text and (text.startswith((' ', '\t')) or text.endswith((' ', '\t'))):
                            if elem.getAttribute("xml:space") != "preserve":
                                elem.setAttribute("xml:space", "preserve")
                                text_preview = repr(text[:30]) + "..." if len(text) > 30 else repr(text)
                                print(f"  Repaired: {xml_file.name}: Added xml:space='preserve' to {elem.tagName}: {text_preview}")
                                repairs += 1
                                modified = True

                if modified:
                    xml_file.write_bytes(dom.toxml(encoding="UTF-8"))

            except Exception:
                pass

        return repairs

    def validate_xml(self):
        """Validate that all XML files are well-formed."""
        errors = []

        for xml_file in self.xml_files:
            try:
                # Try to parse the XML file
                lxml.etree.parse(str(xml_file))
            except lxml.etree.XMLSyntaxError as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: "
                    f"Line {e.lineno}: {e.msg}"
                )
            except Exception as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: "
                    f"Unexpected error: {str(e)}"
                )

        if errors:
            print(f"FAILED - Found {len(errors)} XML violations:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("PASSED - All XML files are well-formed")
            return True

    def validate_namespaces(self):
        """Validate that namespace prefixes in Ignorable attributes are declared."""
        errors = []

        for xml_file in self.xml_files:
            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                declared = set(root.nsmap.keys()) - {None}  # Exclude default namespace

                for attr_val in [
                    v for k, v in root.attrib.items() if k.endswith("Ignorable")
                ]:
                    undeclared = set(attr_val.split()) - declared
                    errors.extend(
                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                        f"Namespace '{ns}' in Ignorable but not declared"
                        for ns in undeclared
                    )
            except lxml.etree.XMLSyntaxError:
                continue

        if errors:
            print(f"FAILED - {len(errors)} namespace issues:")
            for error in errors:
                print(error)
            return False
        if self.verbose:
            print("PASSED - All namespace prefixes properly declared")
        return True

    def validate_unique_ids(self):
        """Validate that specific IDs are unique according to OOXML requirements."""
        errors = []
        global_ids = {}  # Track globally unique IDs across all files

        for xml_file in self.xml_files:
            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                file_ids = {}  # Track IDs that must be unique within this file

                # Remove all mc:AlternateContent elements from the tree
                mc_elements = root.xpath(
                    ".//mc:AlternateContent", namespaces={"mc": self.MC_NAMESPACE}
                )
                for elem in mc_elements:
                    elem.getparent().remove(elem)

                # Now check IDs in the cleaned tree
                for elem in root.iter():
                    # Get the element name without namespace
                    tag = (
                        elem.tag.split("}")[-1].lower()
                        if "}" in elem.tag
                        else elem.tag.lower()
                    )

                    # Check if this element type has ID uniqueness requirements
                    if tag in self.UNIQUE_ID_REQUIREMENTS:
                        # Skip if element is inside an excluded container
                        # (e.g., <p14:sldId> inside <p14:sectionLst> is a reference, not a definition)
                        in_excluded_container = any(
                            ancestor.tag.split("}")[-1].lower() in self.EXCLUDED_ID_CONTAINERS
                            for ancestor in elem.iterancestors()
                        )
                        if in_excluded_container:
                            continue

                        attr_name, scope = self.UNIQUE_ID_REQUIREMENTS[tag]

                        # Look for the specified attribute
                        id_value = None
                        for attr, value in elem.attrib.items():
                            attr_local = (
                                attr.split("}")[-1].lower()
                                if "}" in attr
                                else attr.lower()
                            )
                            if attr_local == attr_name:
                                id_value = value
                                break

                        if id_value is not None:
                            if scope == "global":
                                # Check global uniqueness
                                if id_value in global_ids:
                                    prev_file, prev_line, prev_tag = global_ids[
                                        id_value
                                    ]
                                    errors.append(
                                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                        f"Line {elem.sourceline}: Global ID '{id_value}' in <{tag}> "
                                        f"already used in {prev_file} at line {prev_line} in <{prev_tag}>"
                                    )
                                else:
                                    global_ids[id_value] = (
                                        xml_file.relative_to(self.unpacked_dir),
                                        elem.sourceline,
                                        tag,
                                    )
                            elif scope == "file":
                                # Check file-level uniqueness
                                key = (tag, attr_name)
                                if key not in file_ids:
                                    file_ids[key] = {}

                                if id_value in file_ids[key]:
                                    prev_line = file_ids[key][id_value]
                                    errors.append(
                                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                        f"Line {elem.sourceline}: Duplicate {attr_name}='{id_value}' in <{tag}> "
                                        f"(first occurrence at line {prev_line})"
                                    )
                                else:
                                    file_ids[key][id_value] = elem.sourceline

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: Error: {e}"
                )

        if errors:
            print(f"FAILED - Found {len(errors)} ID uniqueness violations:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("PASSED - All required IDs are unique")
            return True

    def validate_file_references(self):
        """
        Validate that all .rels files properly reference files and that all files are referenced.
        """
        errors = []

        # Find all .rels files
        rels_files = list(self.unpacked_dir.rglob("*.rels"))

        if not rels_files:
            if self.verbose:
                print("PASSED - No .rels files found")
            return True

        # Get all files in the unpacked directory (excluding reference files)
        all_files = []
        for file_path in self.unpacked_dir.rglob("*"):
            if (
                file_path.is_file()
                and file_path.name != "[Content_Types].xml"
                and not file_path.name.endswith(".rels")
            ):  # This file is not referenced by .rels
                all_files.append(file_path.resolve())

        # Track all files that are referenced by any .rels file
        all_referenced_files = set()

        if self.verbose:
            print(
                f"Found {len(rels_files)} .rels files and {len(all_files)} target files"
            )

        # Check each .rels file
        for rels_file in rels_files:
            try:
                # Parse relationships file
                rels_root = lxml.etree.parse(str(rels_file)).getroot()

                # Get the directory where this .rels file is located
                rels_dir = rels_file.parent

                # Find all relationships and their targets
                referenced_files = set()
                broken_refs = []

                for rel in rels_root.findall(
                    ".//ns:Relationship",
                    namespaces={"ns": self.PACKAGE_RELATIONSHIPS_NAMESPACE},
                ):
                    target = rel.get("Target")
                    if target and not target.startswith(
                        ("http", "mailto:")
                    ):  # Skip external URLs
                        # Resolve the target path
                        # Absolute paths (starting with /) are relative to package root
                        # Relative paths are relative to the .rels file's parent directory
                        if target.startswith("/"):
                            # Absolute path - resolve from unpacked_dir root
                            # Strip leading / to avoid pathlib replacing the base
                            target_path = self.unpacked_dir / target.lstrip("/")
                        elif rels_file.name == ".rels":
                            # Root .rels file - relative targets are relative to unpacked_dir
                            target_path = self.unpacked_dir / target
                        else:
                            # Other .rels files - relative targets are relative to their parent's parent
                            # e.g., word/_rels/document.xml.rels -> targets relative to word/
                            base_dir = rels_dir.parent
                            target_path = base_dir / target

                        # Normalize the path and check if it exists
                        try:
                            target_path = target_path.resolve()
                            if target_path.exists() and target_path.is_file():
                                referenced_files.add(target_path)
                                all_referenced_files.add(target_path)
                            else:
                                broken_refs.append((target, rel.sourceline))
                        except (OSError, ValueError):
                            broken_refs.append((target, rel.sourceline))

                # Report broken references
                if broken_refs:
                    rel_path = rels_file.relative_to(self.unpacked_dir)
                    for broken_ref, line_num in broken_refs:
                        errors.append(
                            f"  {rel_path}: Line {line_num}: Broken reference to {broken_ref}"
                        )

            except Exception as e:
                rel_path = rels_file.relative_to(self.unpacked_dir)
                errors.append(f"  Error parsing {rel_path}: {e}")

        # Check for unreferenced files (files that exist but are not referenced anywhere)
        unreferenced_files = set(all_files) - all_referenced_files

        if unreferenced_files:
            for unref_file in sorted(unreferenced_files):
                unref_rel_path = unref_file.relative_to(self.unpacked_dir)
                errors.append(f"  Unreferenced file: {unref_rel_path}")

        if errors:
            print(f"FAILED - Found {len(errors)} relationship validation errors:")
            for error in errors:
                print(error)
            print(
                "CRITICAL: These errors will cause the document to appear corrupt. "
                + "Broken references MUST be fixed, "
                + "and unreferenced files MUST be referenced or removed."
            )
            return False
        else:
            if self.verbose:
                print(
                    "PASSED - All references are valid and all files are properly referenced"
                )
            return True

    def validate_all_relationship_ids(self):
        """
        Validate that all r:id attributes in XML files reference existing IDs
        in their corresponding .rels files, and optionally validate relationship types.
        """
        import lxml.etree

        errors = []

        # Process each XML file that might contain r:id references
        for xml_file in self.xml_files:
            # Skip .rels files themselves
            if xml_file.suffix == ".rels":
                continue

            # Determine the corresponding .rels file
            # For dir/file.xml, it's dir/_rels/file.xml.rels
            rels_dir = xml_file.parent / "_rels"
            rels_file = rels_dir / f"{xml_file.name}.rels"

            # Skip if there's no corresponding .rels file (that's okay)
            if not rels_file.exists():
                continue

            try:
                # Parse the .rels file to get valid relationship IDs and their types
                rels_root = lxml.etree.parse(str(rels_file)).getroot()
                rid_to_type = {}

                for rel in rels_root.findall(
                    f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
                ):
                    rid = rel.get("Id")
                    rel_type = rel.get("Type", "")
                    if rid:
                        # Check for duplicate rIds
                        if rid in rid_to_type:
                            rels_rel_path = rels_file.relative_to(self.unpacked_dir)
                            errors.append(
                                f"  {rels_rel_path}: Line {rel.sourceline}: "
                                f"Duplicate relationship ID '{rid}' (IDs must be unique)"
                            )
                        # Extract just the type name from the full URL
                        type_name = (
                            rel_type.split("/")[-1] if "/" in rel_type else rel_type
                        )
                        rid_to_type[rid] = type_name

                # Parse the XML file to find all r:id references
                xml_root = lxml.etree.parse(str(xml_file)).getroot()

                # Find all elements with r:id attributes
                for elem in xml_root.iter():
                    # Check for r:id attribute (relationship ID)
                    rid_attr = elem.get(f"{{{self.OFFICE_RELATIONSHIPS_NAMESPACE}}}id")
                    if rid_attr:
                        xml_rel_path = xml_file.relative_to(self.unpacked_dir)
                        elem_name = (
                            elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        )

                        # Check if the ID exists
                        if rid_attr not in rid_to_type:
                            errors.append(
                                f"  {xml_rel_path}: Line {elem.sourceline}: "
                                f"<{elem_name}> references non-existent relationship '{rid_attr}' "
                                f"(valid IDs: {', '.join(sorted(rid_to_type.keys())[:5])}{'...' if len(rid_to_type) > 5 else ''})"
                            )
                        # Check if we have type expectations for this element
                        elif self.ELEMENT_RELATIONSHIP_TYPES:
                            expected_type = self._get_expected_relationship_type(
                                elem_name
                            )
                            if expected_type:
                                actual_type = rid_to_type[rid_attr]
                                # Check if the actual type matches or contains the expected type
                                if expected_type not in actual_type.lower():
                                    errors.append(
                                        f"  {xml_rel_path}: Line {elem.sourceline}: "
                                        f"<{elem_name}> references '{rid_attr}' which points to '{actual_type}' "
                                        f"but should point to a '{expected_type}' relationship"
                                    )

            except Exception as e:
                xml_rel_path = xml_file.relative_to(self.unpacked_dir)
                errors.append(f"  Error processing {xml_rel_path}: {e}")

        if errors:
            print(f"FAILED - Found {len(errors)} relationship ID reference errors:")
            for error in errors:
                print(error)
            print("\nThese ID mismatches will cause the document to appear corrupt!")
            return False
        else:
            if self.verbose:
                print("PASSED - All rel

... [Content truncated, total 43,527 chars] ...