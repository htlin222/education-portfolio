from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalListing:
    sfid: str
    student_name: str
    passport_name: str
    form_name: str


@dataclass
class FormMetadata:
    pid: str
    pcid: str
    qfid: str
    sfid: str


@dataclass
class RadioOption:
    value_id: str
    label: str
    is_other: bool = False


@dataclass
class FormField:
    field_type: str
    question_id: str
    label: str
    said: str
    is_required: bool = False


@dataclass
class RadioField(FormField):
    options: list[RadioOption] = field(default_factory=list)

    def __post_init__(self):
        self.field_type = "radio"


@dataclass
class TextField(FormField):
    current_value: str = ""
    is_readonly: bool = False

    def __post_init__(self):
        self.field_type = "text"


@dataclass
class TextareaField(FormField):
    current_value: str = ""

    def __post_init__(self):
        self.field_type = "textarea"


@dataclass
class CheckboxOption:
    value_id: str
    label: str
    is_other: bool = False


@dataclass
class CheckboxField(FormField):
    options: list[CheckboxOption] = field(default_factory=list)

    def __post_init__(self):
        self.field_type = "checkbox"


@dataclass
class ComboField(FormField):
    options: list[RadioOption] = field(default_factory=list)  # reuse RadioOption

    def __post_init__(self):
        self.field_type = "combo"


@dataclass
class DateField(FormField):
    current_value: str = ""

    def __post_init__(self):
        self.field_type = "date"


@dataclass
class RulerRow:
    row_id: str
    label: str
    cells: dict[int, str] = field(default_factory=dict)  # colidx -> option_id


@dataclass
class RulerBlock:
    question_id: str
    label: str
    scale_description: str
    headers: list[str] = field(default_factory=list)  # e.g. ["NA","1","2",...,"9"]
    rows: list[RulerRow] = field(default_factory=list)


@dataclass
class ParsedForm:
    metadata: FormMetadata
    title: str
    student_name: str
    fields: list[FormField] = field(default_factory=list)
    ruler_blocks: list[RulerBlock] = field(default_factory=list)
