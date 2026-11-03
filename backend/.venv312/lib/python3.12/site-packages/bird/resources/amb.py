from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from bird._generated import AMBMessage, AMBMessageSendRequest
from bird._models import to_wire
from bird._types import RequestOptions
from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_gen import AsyncAmbBase, AmbBase
from bird.resources.amb_business_accounts import AsyncAmbBusinessAccounts, AmbBusinessAccounts
from bird.resources.amb_conversations_gen import AsyncAmbConversations, AmbConversations
from bird.resources.amb_routing_rules_gen import AsyncAmbRoutingRules, AmbRoutingRules
from bird.resources.amb_stats import AsyncAmbStats, AmbStats
from bird.resources.amb_suppressions_gen import AsyncAmbSuppressions, AmbSuppressions


class Amb(AmbBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.business_accounts = AmbBusinessAccounts(client)
        self.conversations = AmbConversations(client)
        self.routing_rules = AmbRoutingRules(client)
        self.stats = AmbStats(client)
        self.suppressions = AmbSuppressions(client)

    def send(
        self,
        *,
        from_: str,
        to: str,
        content: Mapping[str, Any],
        source: str | None = None,
        category: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        group: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> AMBMessage:
        """Reply to an open conversation as a configured, connected business account.

        Example:
            message = bird.amb.send(
                from_="b52d6267-2b62-4f8a-8842-0533d0f1dc07",
                to="opaque-customer",
                content={"type": "text", "body": "Your order is ready."},
            )
        """
        body = to_wire(AMBMessageSendRequest, {
            "from": from_, "to": to, "content": content, "source": source,
            "category": category, "metadata": metadata, "tags": tags,
            "group": group, "intent": intent, "locale": locale,
        })
        return self._write("POST", "/v1/amb/messages", body, AMBMessage, options)


class AsyncAmb(AsyncAmbBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.business_accounts = AsyncAmbBusinessAccounts(client)
        self.conversations = AsyncAmbConversations(client)
        self.routing_rules = AsyncAmbRoutingRules(client)
        self.stats = AsyncAmbStats(client)
        self.suppressions = AsyncAmbSuppressions(client)

    async def send(
        self,
        *,
        from_: str,
        to: str,
        content: Mapping[str, Any],
        source: str | None = None,
        category: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        group: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> AMBMessage:
        """Reply to an open conversation as a configured, connected business account.

        Example:
            message = await bird.amb.send(
                from_="b52d6267-2b62-4f8a-8842-0533d0f1dc07",
                to="opaque-customer",
                content={"type": "text", "body": "Your order is ready."},
            )
        """
        body = to_wire(AMBMessageSendRequest, {
            "from": from_, "to": to, "content": content, "source": source,
            "category": category, "metadata": metadata, "tags": tags,
            "group": group, "intent": intent, "locale": locale,
        })
        return await self._write("POST", "/v1/amb/messages", body, AMBMessage, options)


class _AmbSendRequired(TypedDict):
    from_: str
    to: str
    content: Mapping[str, Any]


class AmbSendParams(_AmbSendRequired, total=False):
    source: str
    category: str
    metadata: Mapping[str, Any]
    tags: Sequence[Mapping[str, str]]
    group: str
    intent: str
    locale: str
