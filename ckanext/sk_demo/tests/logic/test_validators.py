"""Tests for ckanext.sk_demo.logic.validators."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.sk_demo.logic import validators


def test_required_with_valid_value():
    """Non-empty value is accepted."""
    assert validators.sk_demo_required("value") == "value"


def test_required_with_invalid_value():
    """Missing value is not accepted."""
    with pytest.raises(tk.Invalid):
        validators.sk_demo_required(None)


def test_complex():
    """Do something complex here."""
    key = ("name",)
    errors = {key: []}

    with pytest.raises(tk.StopOnError):
        validators.sk_demo_complex_validator(
            key,
            {key: tk.missing},
            errors,
            {},
        )

    assert errors[key] == ["Required"]
