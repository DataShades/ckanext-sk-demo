"""Views of the sk_demo plugin.

All blueprints added to `__all__` are registered as blueprints inside Flask
app. If you have multiple blueprints, create them inside submodules of
`ckanext.sk_demo.views` and re-export via `__all__`.

Example:
    ```python
    from .custom import custom_bp
    from .data import data_bp

    __all__ = ["custom_bp", "data_bp"]
    ```
"""

from __future__ import annotations

import datetime
import os
from typing import Any, Generator
import itertools as it
import contextlib
from ckanext.collection.shared import get_collection
from flask import Blueprint

import ckan.plugins.toolkit as tk
from ckan import model
from ckanext.files.utils import IterableBytesReader
from ckanext.files.shared import get_storage, FileData, File
from ckanext.ingest import shared as ingest_shared
from ckanext.ingest.strategy.xlsx import XlsxStrategy
from ckanext.tabledesigner.datastore import create_table
from ckanext.datastore.blueprint import dump_to

__all__ = ["bp"]

bp = Blueprint("sk_demo", __name__)


# instead of catching exceptions inside every view, it's usually more
# convenient to register handlers for the exception class.
@bp.errorhandler(tk.ObjectNotFound)
def not_found_handler(error: tk.ObjectNotFound) -> tuple[str, int]:
    """Generic handler for ObjectNotFound exception."""
    return (
        tk.render(
            "error_document_template.html",
            {
                "code": 404,
                "content": f"Object not found: {error.message}",
                "name": "Not found",
            },
        ),
        404,
    )


# error handler renders standard error page. If you want to render
# view-specific page with a flash message instead, it's better it try/catch
# inside the view.
@bp.errorhandler(tk.NotAuthorized)
def not_authorized_handler(error: tk.NotAuthorized) -> tuple[str, int]:
    """Generic handler for NotAuthorized exception."""
    return (
        tk.render(
            "error_document_template.html",
            {
                "code": 403,
                "content": error.message or "Not authorized to view this page",
                "name": "Not authorized",
            },
        ),
        403,
    )


@bp.route("/dataset/<id>/resource/<resource_id>/files/td_snapshots")
def td_snapshots(id: str, resource_id: str):
    """Files used as a source for tabledesigner of the resource."""
    pkg_dict = tk.get_action("package_show")({}, {"id": id})
    resource = tk.get_action("resource_show")({}, {"id": resource_id})

    files = get_collection(
        "sk_demo_td_snapshots", {"resource_id": resource_id, "id": id}, True
    )
    return tk.render(
        "sk_demo/td_files.html",
        {
            "pkg_dict": pkg_dict,
            "resource": resource,
            "files": files,
        },
    )


@bp.route("/dataset/<id>/resource/<resource_id>/files/td")
def td_files(id: str, resource_id: str):
    """Files used as a source for tabledesigner of the resource."""
    pkg_dict = tk.get_action("package_show")({}, {"id": id})
    resource = tk.get_action("resource_show")({}, {"id": resource_id})

    files = get_collection(
        "sk_demo_td_files", {"resource_id": resource_id, "id": id}, True
    )
    return tk.render(
        "sk_demo/td_files.html",
        {
            "pkg_dict": pkg_dict,
            "resource": resource,
            "files": files,
            "allow_upload": True,
        },
    )


@bp.route(
    "/dataset/<id>/resource/<resource_id>/files/td/ingest-file/<file_id>",
    methods=["POST"],
)
def ingest_td_file(id: str, resource_id: str, file_id: str):
    """Files used as a source for tabledesigner of the resource."""
    ingest_method = tk.request.args.get("method", "insert")
    rows = _get_rows(file_id)

    info = tk.get_action("datastore_info")(
        {},
        {"id": resource_id},
    )
    records = []

    has_custom_pk = any(f.get("tdpkreq") == "pk" for f in info["fields"])
    for idx, record in enumerate(rows, 1):
        record.pop(None, None)
        if not has_custom_pk and ingest_method in ("upsert", "update"):
            record["_id"] = idx

        records.append(record)

    snapshot = None
    if info["meta"]["count"]:
        snapshot = _make_snapshot(resource_id)

    try:
        tk.get_action("datastore_upsert")(
            {},
            {
                "resource_id": resource_id,
                "records": records,
                "method": ingest_method,
            },
        )

    except tk.ValidationError as err:
        if snapshot:
            tk.get_action("files_file_delete")(
                {"ignore_auth": True},
                {"id": snapshot["id"]},
            )
        if "records" in err.error_dict:
            for msg in err.error_dict["records"]:
                tk.h.flash_error(msg)

        else:
            tk.h.flash_error(str(err.error_dict))
    else:
        tk.h.flash_success(tk._("File has been successfully ingested."))

    return tk.redirect_to(
        tk.url_for("sk_demo.td_files", id=id, resource_id=resource_id)
    )


def _make_snapshot(resource_id: str) -> dict[str, Any]:
    stream = dump_to(resource_id, "csv", 0, None, {}, "_id", {}, tk.current_user.name)
    reader = IterableBytesReader(stream)

    info = tk.get_action("datastore_info")(
        {},
        {"id": resource_id},
    )

    snapshot = tk.get_action("files_file_create")(
        {"ignore_auth": True},
        {
            "storage": "td_snapshot",
            "name": f"{datetime.datetime.now().isoformat()}.csv",
            "upload": reader.read(),
        },
    )
    file = model.Session.get(File, snapshot["id"])
    file.plugin_data = dict(file.plugin_data, datastore_info=info)
    model.Session.commit()

    return tk.get_action("files_transfer_ownership")(
        {"ignore_auth": True},
        {
            "id": snapshot["id"],
            "owner_id": resource_id,
            "owner_type": "resource",
        },
    )


def _get_rows(file_id: str, storage_name: str = "td") -> Generator[dict[str, Any]]:
    storage = get_storage(storage_name)
    file_dict = tk.get_action("files_file_show")({}, {"id": file_id})

    stream = storage.stream(FileData.from_dict(file_dict))
    source = ingest_shared.make_storage(stream)
    handler = ingest_shared.get_handler_for_mimetype(file_dict["content_type"], source)

    if not handler:
        _name, ext = os.path.splitext(file_dict["name"])
        if ext == ".xlsx":
            handler = ingest_shared.strategies["ingest:xlsx"]()

        elif ext == ".json":
            handler = ingest_shared.strategies["ingest:json_list"]()

        else:
            return tk.abort(422, tk._("Unknown source type"))

    for record in handler.extract(
        source,
        ingest_shared.StrategyOptions(extras={"skip_empty": True, "with_header": True}),
    ):
        if isinstance(handler, XlsxStrategy):
            yield record.raw["row"]
        else:
            yield record.raw


@bp.route(
    "/dataset/<id>/resource/<resource_id>/files/td/reset-file/<file_id>",
    methods=["POST"],
)
def reset_td_file(id: str, resource_id: str, file_id: str):
    """Files used as a source for tabledesigner of the resource."""
    rows = _get_rows(file_id)

    item = next(rows, None)
    if not item:
        tk.h.flash_error("Cannot detect any records in source")
        return tk.redirect_to(
            tk.url_for("sk_demo.td_files", id=id, resource_id=resource_id)
        )

    names: list[str] = [k for k in item if k]

    types: dict[str, set[type]] = {name: set() for name in names}

    chain = it.chain([item], rows)
    for row in chain:
        for name in names:
            if row[name] is None:
                continue
            types[name].add(type(row[name]))

    final_types = {}

    for k, v in types.items():
        if v in ({int, float}, {float}):
            final_types[k] = "numeric"
        elif v in ({datetime.datetime, datetime.date}, {datetime.datetime}):
            final_types[k] = "timestamp"
        elif v == {datetime.date}:
            final_types[k] = "date"
        elif v == {bool}:
            final_types[k] = "boolean"
        elif v == {int}:
            final_types[k] = "integer"
        else:
            final_types[k] = "text"

    fields: list[dict[str, Any]] = [
        {
            "id": field,
            "tdpkreq": "",
            "tdtype": final_types[field],
            "type": final_types[field],
        }
        for field in names
    ]

    with contextlib.suppress(tk.ObjectNotFound):
        tk.get_action("datastore_delete")(
            {},
            {
                "resource_id": resource_id,
            },
        )
    create_table(resource_id, fields)
    tk.h.flash_success(
        tk._(
            "All records were removed and columns recreated according to selected file."
        )
    )
    return tk.redirect_to(
        tk.url_for("sk_demo.td_files", id=id, resource_id=resource_id)
    )


@bp.route(
    "/dataset/<id>/resource/<resource_id>/files/td/restore-snapshot/<file_id>",
    methods=["POST"],
)
def restore_td_snapshot(id: str, resource_id: str, file_id: str):
    """Files used as a source for tabledesigner of the resource."""
    snapshot = tk.get_action("files_file_show")(
        {"include_plugin_data": True}, {"id": file_id}
    )
    try:
        fields = snapshot["plugin_data"]["datastore_info"]["fields"]
    except KeyError:
        return tk.abort(422, tk._("Snapshot is broken"))

    rows = _get_rows(file_id, "td_snapshot")

    with contextlib.suppress(tk.ObjectNotFound):
        tk.get_action("datastore_delete")(
            {},
            {
                "resource_id": resource_id,
            },
        )
    create_table(resource_id, fields)

    tk.get_action("datastore_upsert")(
        {},
        {
            "resource_id": resource_id,
            "records": rows,
            "method": "upsert",
        },
    )

    tk.h.flash_success(tk._("Snapshot restored and can be safely deleted."))
    return tk.redirect_to(
        tk.url_for("sk_demo.td_snapshots", id=id, resource_id=resource_id)
    )
