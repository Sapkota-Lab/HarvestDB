from __future__ import annotations

from typing import Any, Mapping

import pydantic

from bird._exceptions import BirdError


class BaseModel(pydantic.BaseModel):
    """Base for every generated wire model.

    Forward-compatible by default: a field the server adds later is
    accepted and preserved rather than raising, so an older SDK keeps working
    against a newer API. The generator sets ``extra="allow"`` on each model via
    ``--extra-fields``; this base reasserts it and adds the config the facade needs.
    """

    model_config = pydantic.ConfigDict(
        extra="allow",
        populate_by_name=True,  # facade builds requests by field name (e.g. from_)
        validate_default=True,  # coerce enum defaults so a dump never warns
    )


def _validate(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> pydantic.BaseModel:
    """Validate request fields through the generated model, re-raising a client-side
    ``pydantic.ValidationError`` as a ``BirdError`` so everything the SDK raises is a
    ``BirdError`` — and never collides with the SDK's own ``ValidationError`` (a 422
    server response). The message reports which field failed and why (field path +
    reason) but never the offending value, so a caller logging the error can't leak
    recipient/subject content; the original validation error is preserved as
    ``__cause__``.
    """
    try:
        return model_cls.model_validate(dict(data))
    except pydantic.ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        raise BirdError(f"invalid request: {reasons}") from exc


def to_wire(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate request fields through the generated model, then emit wire JSON.

    ``by_alias`` maps ``from_`` to the wire field ``from``; ``exclude_none`` drops
    unset fields so the server applies its defaults.
    """
    return _validate(model_cls, data).model_dump(by_alias=True, exclude_none=True, mode="json")


def to_wire_exclude_unset(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> dict[str, Any]:
    """Like :func:`to_wire`, but drops fields the caller did not set rather than
    ``None`` ones. Use this where a generated model gives an optional field a
    non-``None`` default (e.g. ``DomainSettings`` toggles default to ``False``,
    ``DomainDKIMConfig.mode`` to ``"txt"``): ``exclude_none`` would let that default
    leak onto a partial update, whereas ``exclude_unset`` sends only what the caller
    passed. It also preserves an explicit ``None`` the caller did set — e.g. a
    ``DomainUpdate`` with ``tracking=None`` emits ``"tracking": null`` to remove it.
    """
    return _validate(model_cls, data).model_dump(by_alias=True, exclude_unset=True, mode="json")
