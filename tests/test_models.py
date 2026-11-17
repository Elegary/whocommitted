from whocommitted.models import Identity, RepoRef, Role, Signature


def test_identity_without_names() -> None:
    identity = Identity(email="x@y.z")
    identity.add("sha", Signature("", "x@y.z", Role.AUTHOR))
    assert identity.name == ""
    assert identity.first_seen is None


def test_identity_name_tie_is_deterministic() -> None:
    identity = Identity(email="x@y.z", names={"B": 1, "A": 1})
    assert identity.name == "B"


def test_display_name_falls_back_to_url() -> None:
    assert RepoRef(provider="git", clone_url="file:///r").display_name == "file:///r"
