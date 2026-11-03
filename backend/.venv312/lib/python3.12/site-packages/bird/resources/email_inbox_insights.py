from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_inbox_insights_gen import AsyncEmailInboxInsightsBase, EmailInboxInsightsBase
from bird.resources.email_inbox_insights_domains_gen import AsyncEmailInboxInsightsDomains, EmailInboxInsightsDomains
from bird.resources.email_inbox_insights_domain_monitoring_gen import AsyncEmailInboxInsightsDomainMonitoring, EmailInboxInsightsDomainMonitoring
from bird.resources.email_inbox_insights_benchmarks_gen import AsyncEmailInboxInsightsBenchmarks, EmailInboxInsightsBenchmarks


class EmailInboxInsights(EmailInboxInsightsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.domains = EmailInboxInsightsDomains(client)
        self.domain_monitoring = EmailInboxInsightsDomainMonitoring(client)
        self.benchmarks = EmailInboxInsightsBenchmarks(client)


class AsyncEmailInboxInsights(AsyncEmailInboxInsightsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.domains = AsyncEmailInboxInsightsDomains(client)
        self.domain_monitoring = AsyncEmailInboxInsightsDomainMonitoring(client)
        self.benchmarks = AsyncEmailInboxInsightsBenchmarks(client)
