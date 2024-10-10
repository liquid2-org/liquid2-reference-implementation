import json
import re
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Sequence


@dataclass
class Case:
    """Test case dataclass to help with table driven tests."""

    description: str
    template: str
    expect: str
    globals: dict[str, Any] = field(default_factory=dict)  # noqa: A003
    partials: dict[str, Any] = field(default_factory=dict)
    standard: bool = True
    error: bool = False
    strict: bool = False
    future: bool = False


@dataclass
class NewCase:
    """Test helper class."""

    name: str
    template: str
    data: dict[str, Any] = field(default_factory=dict)
    templates: dict[str, str] | None = None
    result: str | None = None
    invalid: bool | None = None
    tags: list[str] = field(default_factory=list)


def migrate_one(old: Case) -> NewCase:
    if old.error:
        return NewCase(
            name=old.description,
            template=old.template,
            templates=old.partials,
            invalid=old.error,
        )
    return NewCase(
        name=old.description,
        template=old.template,
        data=old.globals,
        templates=old.partials,
        result=old.expect,
        invalid=old.error,
    )


def migrate(cases: Sequence[Case]) -> str:
    new_cases = [asdict(migrate_one(case)) for case in cases]
    return json.dumps({"tests": new_cases}, indent=2)


def asdict(case: NewCase) -> dict[str, Any]:
    if case.invalid:
        d = {
            "name": case.name,
            "template": case.template,
            "invalid": case.invalid,
        }
    else:
        d = {
            "name": case.name,
            "template": case.template,
            "data": case.data,
            "result": case.result,
        }

    if case.templates:
        d["templates"] = case.templates

    return d


RE_CASES = re.compile(r"cases = (\[.+\])\s+", re.DOTALL)


def extract_cases(source: str) -> list[Case]:
    match = RE_CASES.search(source)
    if not match:
        raise Exception(f"failed: {source[:source.find("\n")]}")

    namespace: dict[str, Any] = {"Case": Case}
    return eval(match.group(1), namespace)  # type: ignore


def files(path: Path) -> list[Path]:
    return sorted(path.glob("*_filter.py"))


PROJECT_ROOT = Path(__file__).parent
OUT_PATH = PROJECT_ROOT / "python/tests/liquid2-compliance-test-suite/tests/filters"


def extract(path: Path) -> None:
    with path.open() as fd:
        cases = extract_cases(fd.read())

    filter_name = path.stem.rsplit("_", 1)[0]
    out_path = OUT_PATH / (filter_name + ".json")

    sys.stderr.write(f"Writing {len(cases)} to {out_path}..\n")

    with out_path.open("w") as fd:
        fd.write(migrate(cases))
        fd.write("\n")


if __name__ == "__main__":
    # print(migrate(cases))
    filter_files = files(Path(sys.argv[1]))
    print(filter_files[0])
    extract(filter_files[0])
