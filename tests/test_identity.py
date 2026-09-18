"""Tests for the shared identity readers.

The reader's whole job is to produce the string a machine will report, so the interesting cases
are the ones where it must refuse rather than guess.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from software_update_publisher._contracts import ArtifactClass
from software_update_publisher.exceptions import IdentityError
from software_update_publisher.identity import read_identity, read_msi_identity


class TestDispatch:
    @pytest.mark.parametrize(
        "artifact_class",
        [ArtifactClass.ARCHIVE, ArtifactClass.EXE, ArtifactClass.BURN_EXE, ArtifactClass.NUPKG],
    )
    def test_refuses_a_class_with_no_shared_reader(self, artifact_class: ArtifactClass, tmp_path: Path) -> None:
        # An archive registers nothing at all; inventing a version for one produces a pin no
        # machine can ever satisfy.
        with pytest.raises(IdentityError, match="no shared identity reader"):
            read_identity(artifact_class, tmp_path / "artifact")

    def test_msi_is_the_class_served_here(self, tmp_path: Path) -> None:
        artifact = tmp_path / "not-really.msi"
        artifact.write_bytes(b"this is not a compound file")
        # It reaches the MSI reader rather than the "no reader" refusal: the failure comes
        # from parsing the bytes, not from dispatch.
        with pytest.raises(Exception, match=r"(?i)^(?!.*no shared identity reader).*"):
            read_identity(ArtifactClass.MSI, artifact)


class TestMsiConformance:
    """Pin the reader's output against a real artifact.

    The MSI reader is a pre-release dependency. If it ever returns something different for
    the same bytes, the symptom would be a wrong pin on a live console rather than a crash,
    so the exact values are asserted here.
    """

    @pytest.fixture
    def artifact(self) -> Path:
        return Path(__file__).parent / "fixtures" / "7-zip-26.02.00.0-x64.msi"

    def test_reads_the_version_add_remove_programs_will_report(self, artifact: Path) -> None:
        assert read_msi_identity(artifact).display_version == "26.02.00.0"

    def test_reads_the_publisher_and_product_name(self, artifact: Path) -> None:
        identity = read_msi_identity(artifact)
        assert identity.publisher == "Igor Pavlov"
        assert identity.display_name == "7-Zip 26.02 (x64 edition)"

    def test_reads_the_product_code(self, artifact: Path) -> None:
        assert read_msi_identity(artifact).product_code == "{23170F69-40C1-2702-2602-000001000000}"

    def test_the_product_name_is_not_the_pin_key(self, artifact: Path) -> None:
        # The consumer spells this product Igor-Pavlov_7-Zip. The version is extractable;
        # the name is not, which is why a module declares its identity and extracts only
        # its version.
        assert read_msi_identity(artifact).display_name != "7-Zip"

    def test_dispatches_through_the_class_registry(self, artifact: Path) -> None:
        assert read_identity(ArtifactClass.MSI, artifact).display_version == "26.02.00.0"


class TestMsiReader:
    def test_a_file_that_is_not_an_msi_fails_loudly(self, tmp_path: Path) -> None:
        artifact = tmp_path / "error-page.msi"
        artifact.write_bytes(b"<html>404</html>")
        # A vendor serving an error page under an installer's name is the realistic path here.
        with pytest.raises(Exception):  # noqa: B017, PT011 - the reader surfaces the parser's own error
            read_msi_identity(artifact)
