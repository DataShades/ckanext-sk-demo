from __future__ import annotations

from typing import Any

import factory
import pytest
from pytest_factoryboy import register

from ckan.tests.factories import CKANFactory

from ckanext.sk_demo.model import Something


@pytest.fixture()
def clean_db(reset_db: Any, migrate_db_for: Any):
    """Apply plugin migrations whenever CKAN DB is cleaned."""
    reset_db()
    migrate_db_for("sk_demo")


@register
class SomethingFactory(CKANFactory):
    """Factory fixture for Something objects."""

    class Meta:
        model = Something
        action = "sk_demo_something_create"

    hello = factory.Faker("word")
    world = factory.Faker("word")
    plugin_data = factory.Faker("pydict", value_types=[str, int, bool])
