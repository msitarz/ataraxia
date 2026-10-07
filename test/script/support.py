# SPDX-License-Identifier: Apache-2.0
"""Small process fixtures for the repository's registry selection boundary."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from script.registry_selection import (
    Package as Package,
)
from script.registry_selection import (
    PackagePayload as PackagePayload,
)
from script.registry_selection import (
    accepted_preparation as accepted_preparation,
)
from script.registry_selection import (
    dependency_declarations as dependency_declarations,
)
from script.registry_selection import (
    package_payload as package_payload,
)
from script.registry_selection import (
    preparation_evidence as preparation_evidence,
)
from script.registry_selection import (
    validate_digest as validate_digest,
)
from script.registry_selection import (
    validate_package_layout as validate_package_layout,
)
from script.registry_selection import (
    validate_payload_metadata as validate_payload_metadata,
)
from script.registry_selection import (
    validate_selected_inventory as validate_selected_inventory,
)
from script.registry_selection import (
    validate_wheel_link as validate_wheel_link,
)
from test.script.selection_manifest import (
    select_prepared as select_prepared,
)
from test.script.selection_process import (
    run_selection_cli as run_selection_cli,
)
from test.script.selection_process import (
    tree_state as tree_state,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ChangingRecordRead:
    """Honest filesystem edge: a later record read sees a different fixture file."""

    record: Path
    replacement: Path
    reader: Callable[[Path], bytes]
    record_reads: int = 0

    def read(self, path: Path) -> bytes:
        """Delegate actual file reads, changing only the second record read."""
        if path == self.record:
            self.record_reads += 1
            if self.record_reads > 1:
                return self.reader(self.replacement)
        return self.reader(path)
