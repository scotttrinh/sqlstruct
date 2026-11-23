import sqlstruct


# @lat: [[tests#Tests#Package import]]
def test_package_import() -> None:
    assert hasattr(sqlstruct, "__all__")
