from __future__ import annotations

from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckanext.collection import shared


class Collection(p.SingletonPlugin):
    """Customize dataset lifecycle."""

    p.implements(shared.ICollection, inherit=True)

    def get_collection_factories(self) -> dict[str, shared.types.CollectionFactory]:
        """Register named collection factories.

        Example:
            ```python
            def get_collection_factories(self) -> dict[str, CollectionFactory]:
                return {
                    "packages": PackageCollection,
                }
            ```

        Returns:
            mapping of global collection name to collection factory


        """
        return {
            "sk_demo_td_files": TdFilesCollection,
            "sk_demo_td_snapshots": TdSnapshotsCollection,
            "sk_demo_data_enrichment": EnrichmentCollection,
        }


class FilesData(shared.data.ApiSearchData["dict[str, Any]", "TdFilesCollection"]):
    action = "files_file_search"
    owner_type = "resource"
    storage = "td"
    owner_field_name = "resource_id"

    def get_filters(self) -> dict[str, Any]:
        return {
            "owner_id": self.attached.params.get(self.owner_field_name),
            "owner_type": self.owner_type,
            "storage": self.storage,
        }

    def get_sort(self) -> dict[str, Any]:
        return {"sort": "ctime", "reverse": True}


FilesSerializer = shared.serialize.HtmxTableSerializer.with_attributes(
    ensure_dictized=True,
    record_template="sk_demo/snippets/td_collection_record.html",
    filter_template="sk_demo/snippets/td_collection_filter.html",
)


class TdFilesCollection(shared.collection.ApiSearchCollection):
    DataFactory = FilesData
    SerializerFactory = FilesSerializer
    ColumnsFactory = shared.columns.Columns.with_attributes(
        names=["name", "ctime", "actions"],
        labels={"name": "Filename", "ctime": "Creation time", "actions": "Actions"},
        serializers={
            "ctime": [
                (lambda v, o, n, r, s: tk.h.render_datetime(v, with_hours=True), {})
            ]
        },
    )


class TdSnapshotsCollection(shared.collection.ApiSearchCollection):
    DataFactory = FilesData.with_attributes(storage="td_snapshot")
    SerializerFactory = FilesSerializer.with_attributes(
        record_template="sk_demo/snippets/td_snapshot_collection_record.html",
    )
    ColumnsFactory = shared.columns.Columns.with_attributes(
        names=["ctime", "actions"],
        labels={"ctime": "Creation time", "actions": "Actions"},
        serializers={
            "ctime": [
                (
                    lambda v, o, n, r, s: tk.h.render_datetime(
                        v, with_hours=True, with_seconds=True
                    ),
                    {},
                )
            ]
        },
    )


class EnrichmentCollection(shared.collection.ApiSearchCollection):
    DataFactory = FilesData.with_attributes(
        storage="data_enrichment",
        owner_field_name="id",
        owner_type="package",
    )
    SerializerFactory = FilesSerializer.with_attributes(
        record_template="sk_demo/snippets/data_enrichment_collection_record.html",
    )
    ColumnsFactory = shared.columns.Columns.with_attributes(
        names=["name", "ctime", "actions"],
        labels={"name": "Filename", "ctime": "Creation time", "actions": "Actions"},
        serializers={
            "ctime": [
                (lambda v, o, n, r, s: tk.h.render_datetime(v, with_hours=True), {})
            ]
        },
    )


# [value:Any, options:"dict[str, Any]", name:str, record:Any, self:BaseSerializer]
