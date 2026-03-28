from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

import requests

from evalbot.models import (
    CheckboxField,
    CheckboxOption,
    ComboField,
    DateField,
    FormField,
    FormMetadata,
    ParsedForm,
    RadioField,
    RadioOption,
    RulerBlock,
    RulerRow,
    TextField,
    TextareaField,
)
from evalbot.session import get


def fetch_and_parse(session: requests.Session, sfid: str) -> ParsedForm:
    resp = get(session, f"oneEvaluate?sfid={sfid}")
    resp.raise_for_status()
    return parse_form_html(resp.text, sfid)


def parse_form_html(html: str, sfid: str) -> ParsedForm:
    soup = BeautifulSoup(html, "html.parser")

    metadata = _parse_metadata(soup, sfid)
    title = _parse_title(soup)
    student_name = _parse_student_name(soup)
    fields = _parse_fields(soup)
    ruler_blocks = _parse_ruler_blocks(soup)

    return ParsedForm(
        metadata=metadata,
        title=title,
        student_name=student_name,
        fields=fields,
        ruler_blocks=ruler_blocks,
    )


def _parse_metadata(soup: BeautifulSoup, sfid: str) -> FormMetadata:
    def val(id_: str) -> str:
        el = soup.find("input", id=id_)
        return el["value"] if el else ""

    return FormMetadata(
        pid=val("pid"),
        pcid=val("pcid"),
        qfid=val("qfid"),
        sfid=val("sfid") or sfid,
    )


def _parse_title(soup: BeautifulSoup) -> str:
    header = soup.find("h3") or soup.find("h2")
    if header:
        return header.get_text(strip=True)
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else ""


def _parse_student_name(soup: BeautifulSoup) -> str:
    # Look for student name in the page header area
    for el in soup.find_all(["h4", "h3", "span"]):
        text = el.get_text(strip=True)
        if "學員" in text or "姓名" in text:
            # Try to extract name from nearby elements
            parent = el.find_parent("div", class_="form-group")
            if parent:
                val_div = parent.find("div", class_=re.compile(r"col-md-9|col-sm-7"))
                if val_div:
                    return val_div.get_text(strip=True)
    return ""


def _parse_fields(soup: BeautifulSoup) -> list[FormField]:
    fields: list[FormField] = []
    form = soup.find("form", class_="qa-list")
    if not form:
        return fields

    for group in form.find_all("div", class_="form-group"):
        # Get label
        label_div = group.find("div", class_="control-label")
        if not label_div:
            continue
        label = label_div.get_text(strip=True).replace("＊", "").replace("*", "").strip()
        # Remove the 師/生 badge text from label
        for badge in label_div.find_all("span", class_="label"):
            badge_text = badge.get_text(strip=True)
            label = label.replace(badge_text, "").strip()

        # Check if this is a teacher-editable field
        value_div = group.find("div", class_=re.compile(r"col-md-9|col-sm-7"))
        if not value_div:
            continue

        classes = value_div.get("class", [])
        is_teacher_field = "myown" in classes

        if not is_teacher_field:
            continue

        is_required = "mustkey" in classes

        # Get SAID
        said_span = value_div.find("span", class_="hsaid")
        said = said_span.get_text(strip=True) if said_span else ""

        # Detect field type
        radios = value_div.find_all("input", type="radio")
        checkboxes = value_div.find_all("input", type="checkbox")
        textarea = value_div.find("textarea")
        select = value_div.find("select")
        date_input = value_div.find("input", class_="datepicker") or value_div.find(
            "input", attrs={"onblur": re.compile(r"updAdate")}
        )
        text_input = value_div.find("input", type="text")

        if radios:
            field = _parse_radio(radios, label, said, is_required)
            if field:
                fields.append(field)
        elif checkboxes:
            field = _parse_checkbox(checkboxes, label, said, is_required)
            if field:
                fields.append(field)
        elif textarea:
            field = _parse_textarea(textarea, label, said, is_required)
            if field:
                fields.append(field)
        elif select:
            field = _parse_combo(select, label, said, is_required)
            if field:
                fields.append(field)
        elif date_input:
            field = _parse_date(date_input, label, said, is_required)
            if field:
                fields.append(field)
        elif text_input:
            field = _parse_text(text_input, label, said, is_required)
            if field:
                fields.append(field)

    return fields


def _parse_radio(
    radios: list[Tag], label: str, said: str, is_required: bool
) -> RadioField | None:
    if not radios:
        return None

    # Extract QID from onclick handler
    qid = ""
    for r in radios:
        onclick = r.get("onclick", "")
        m = re.search(r"updAradio\(this,\s*(\d+)\)", onclick)
        if m:
            qid = m.group(1)
            break
    if not qid:
        # Try from name attribute
        name = radios[0].get("name", "")
        m = re.match(r"rdo(\d+)", name)
        if m:
            qid = m.group(1)

    if not qid:
        return None

    options: list[RadioOption] = []
    for r in radios:
        opt_label = ""
        parent_label = r.find_parent("label")
        if parent_label:
            opt_label = parent_label.get_text(strip=True)
        options.append(
            RadioOption(
                value_id=r.get("value", ""),
                label=opt_label,
                is_other=r.get("data-isoth", "0") == "1",
            )
        )

    return RadioField(
        field_type="radio",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        options=options,
    )


def _parse_checkbox(
    checkboxes: list[Tag], label: str, said: str, is_required: bool
) -> CheckboxField | None:
    if not checkboxes:
        return None

    # Extract QID from onclick handler
    qid = ""
    for cb in checkboxes:
        onclick = cb.get("onclick", "")
        m = re.search(r"updAcheck\(this,\s*(\d+)\)", onclick)
        if m:
            qid = m.group(1)
            break
    if not qid:
        return None

    options: list[CheckboxOption] = []
    for cb in checkboxes:
        opt_label = ""
        parent_label = cb.find_parent("label")
        if parent_label:
            opt_label = parent_label.get_text(strip=True)
        options.append(
            CheckboxOption(
                value_id=cb.get("value", ""),
                label=opt_label,
                is_other=cb.get("data-isoth", "0") == "1",
            )
        )

    return CheckboxField(
        field_type="checkbox",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        options=options,
    )


def _parse_combo(
    select: Tag, label: str, said: str, is_required: bool
) -> ComboField | None:
    # Extract QID from onchange handler
    qid = ""
    onchange = select.get("onchange", "")
    m = re.search(r"updCombo\(this,\s*(\d+)\)", onchange)
    if m:
        qid = m.group(1)

    if not qid:
        return None

    options: list[RadioOption] = []
    for opt in select.find_all("option"):
        value = opt.get("value", "")
        if not value:
            continue  # skip placeholder options
        options.append(
            RadioOption(
                value_id=value,
                label=opt.get_text(strip=True),
            )
        )

    return ComboField(
        field_type="combo",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        options=options,
    )


def _parse_date(
    date_input: Tag, label: str, said: str, is_required: bool
) -> DateField | None:
    # Extract QID from onblur handler
    qid = date_input.get("data-qid", "")
    if not qid:
        onblur = date_input.get("onblur", "")
        m = re.search(r"updAdate\(this,\s*(\d+)\)", onblur)
        if m:
            qid = m.group(1)

    if not qid:
        return None

    return DateField(
        field_type="date",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        current_value=date_input.get("value", ""),
    )


def _parse_text(
    text_input: Tag, label: str, said: str, is_required: bool
) -> TextField | None:
    is_readonly = text_input.has_attr("readonly")

    # Extract QID
    qid = text_input.get("data-qid", "")
    if not qid:
        onblur = text_input.get("onblur", "")
        m = re.search(r"updAtext\(this,\s*(\d+)\)", onblur)
        if m:
            qid = m.group(1)
    if not qid:
        onclick = text_input.get("onclick", "")
        m = re.search(r"putUsername\(this,\s*'[^']*',\s*(\d+)\)", onclick)
        if m:
            qid = m.group(1)

    if not qid:
        return None

    return TextField(
        field_type="text",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        current_value=text_input.get("value", ""),
        is_readonly=is_readonly,
    )


def _parse_textarea(
    textarea: Tag, label: str, said: str, is_required: bool
) -> TextareaField | None:
    qid = ""
    onblur = textarea.get("onblur", "")
    m = re.search(r"updAtext2?\(this,\s*(\d+)\)", onblur)
    if m:
        qid = m.group(1)

    if not qid:
        return None

    return TextareaField(
        field_type="textarea",
        question_id=qid,
        label=label,
        said=said,
        is_required=is_required,
        current_value=textarea.get_text(strip=True),
    )


def _parse_ruler_blocks(soup: BeautifulSoup) -> list[RulerBlock]:
    blocks: list[RulerBlock] = []

    for blk in soup.find_all("div", class_=re.compile(r"rulblk\d")):
        table = blk.find("table", class_="rulertable")
        if not table:
            continue

        # QID from save button
        qid = ""
        btn = blk.find("button", onclick=re.compile(r"tmpSaveRuler"))
        if btn:
            m = re.search(r"tmpSaveRuler2?\(this,\s*(\d+)\)", btn.get("onclick", ""))
            if m:
                qid = m.group(1)

        # Label
        h4 = blk.find("h4")
        label = h4.get_text(strip=True) if h4 else ""

        # Scale description from <small>
        small = blk.find("small")
        scale_desc = small.get_text(strip=True) if small else ""

        # Headers
        headers: list[str] = []
        thead = table.find("thead")
        if thead:
            for th in thead.find_all("th", class_="ruleranswer"):
                headers.append(th.get_text(strip=True))

        # Rows
        rows: list[RulerRow] = []
        tbody = table.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr"):
                left = tr.find("td", class_="quesleft")
                if not left:
                    continue
                row_id = left.get("data-value", "")
                row_label = left.get_text(strip=True)

                cells: dict[int, str] = {}
                for cell in tr.find_all("td", class_="rulerpointer"):
                    colidx = int(cell.get("data-colidx", 0))
                    option_id = cell.get("data-value", "")
                    cells[colidx] = option_id

                rows.append(RulerRow(row_id=row_id, label=row_label, cells=cells))

        blocks.append(
            RulerBlock(
                question_id=qid,
                label=label,
                scale_description=scale_desc,
                headers=headers,
                rows=rows,
            )
        )

    return blocks
