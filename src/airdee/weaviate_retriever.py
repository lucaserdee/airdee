from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal

import weaviate
from weaviate.classes.query import Filter as WvFilter, Sort as WvSort


@dataclass
class SortSpec:
    path: str
    order: Literal["asc", "desc"] = "desc"


class WeaviateRetriever:
    """
    Weaviate v4 retriever using Collections API.
    """

    def __init__(self, client: weaviate.WeaviateClient) -> None:
        self.client = client

    def search(
        self,
        class_name: str,
        *,
        fulltext: Optional[str] = None,          # reserved for later (bm25)
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[SortSpec] | List[Dict[str, Any]] | Dict[str, Any] | SortSpec] = None,
        limit: int = 5,
        select: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query a class and return list of dicts (properties + _meta.id).
        """
        props = select or ["rdId", "title", "lead", "body", "publishedAt", "source", "tags", "mainCategory"]
        col = self.client.collections.get(class_name)

        wv_where = self._filters_to_where(filters)
        wv_sort  = self._sort_to_v4(sort)

        # If you add BM25 later, switch to col.query.bm25(...). For now, plain fetch:
        result = col.query.fetch_objects(
            limit=limit,
            return_properties=props,
            filters=wv_where,
            sort=wv_sort,  # v4 expects a single _Sorting or None
        )

        items: List[Dict[str, Any]] = []
        for obj in (getattr(result, "objects", []) or []):
            data = dict(obj.properties or {})
            data["_meta"] = {"id": str(obj.uuid)}
            items.append(data)
        return items

    # ----------------- helpers -----------------

    def _sort_to_v4(
        self,
        sort: Optional[List[SortSpec] | List[Dict[str, Any]] | Dict[str, Any] | SortSpec]
    ):
        """
        Convert incoming sort (often a list) into a single v4 _Sorting.
        v4 public API accepts one _Sorting object; if multiple provided, we take the first.
        """
        if not sort:
            return None

        # Normalize to one item
        first = sort[0] if isinstance(sort, list) else sort

        if isinstance(first, dict):
            path = first.get("path")
            order = (first.get("order") or "desc").lower()
        else:
            path = getattr(first, "path", None)
            order = getattr(first, "order", "desc").lower()

        if not path:
            return None

        return WvSort.by_property(path, ascending=(order == "asc"))

    def _filters_to_where(self, filters: Optional[Dict[str, Any]]) -> Optional[WvFilter]:
        """
        Build a v4 Filter tree.

        Supports either:
          A) Per-field style (AND across fields):
             {
               "publishedAt": {"gte": "2024-01-01T00:00:00Z", "lte": "2024-12-31T23:59:59Z"},
               "isLiveblog": false
             }

          B) Explicit single-clause style:
             {
               "path": "publishedAt",
               "operator": "GreaterThanEqual",
               "value": "2024-06-01T00:00:00Z"
             }
        """
        if not filters:
            return None

        # If explicit single-clause style detected
        if "path" in filters and "operator" in filters:
            return self._single_clause(filters["path"], filters["operator"], filters.get("value"))

        # Otherwise assume per-field dict; combine all with AND
        clauses: List[WvFilter] = []
        for field, value in filters.items():
            if isinstance(value, dict):
                # multiple ops on same field AND-ed
                sub: Optional[WvFilter] = None
                for op, v in value.items():
                    c = self._apply_op(field, op, v)
                    sub = c if sub is None else (sub & c)
                if sub is not None:
                    clauses.append(sub)
            else:
                # equality by default
                clauses.append(WvFilter.by_property(field).equal(value))

        if not clauses:
            return None

        expr = clauses[0]
        for c in clauses[1:]:
            expr = expr & c
        return expr

    def _single_clause(self, path: str, operator: str, value: Any) -> WvFilter:
        """Map one explicit operator clause to a v4 Filter."""
        f = WvFilter.by_property(path)
        op = operator.strip().lower()

        # Accept common spellings/cases
        if op in ("equal", "eq"):                      return f.equal(value)
        if op in ("notequal", "neq"):                  return f.not_equal(value)
        if op in ("greaterthan", "gt"):                return f.greater_than(value)
        if op in ("greaterthanequal", "gte", "ge"):    return f.greater_or_equal(value)
        if op in ("lessthan", "lt"):                   return f.less_than(value)
        if op in ("lessthanequal", "lte", "le"):       return f.less_or_equal(value)
        if op in ("like",):                            return f.like(str(value))

        raise ValueError(f"Unsupported operator: {operator}")

    def _apply_op(self, field: str, op_key: str, value: Any) -> WvFilter:
        """Handle compact per-field ops like {'gte': ..., 'lte': ...}."""
        f = WvFilter.by_property(field)
        k = op_key.strip().lower()
        if k == "eq":   return f.equal(value)
        if k == "neq":  return f.not_equal(value)
        if k == "gt":   return f.greater_than(value)
        if k == "gte":  return f.greater_or_equal(value)
        if k == "lt":   return f.less_than(value)
        if k == "lte":  return f.less_or_equal(value)
        if k == "like": return f.like(str(value))
        # default to equality to be forgiving
        return f.equal(value)
