from typing import Callable, Optional
from scorebrowser.synchronization import (
    ReauthRequired,
    UpstreamError,
    UpstreamScore,
    UpstreamScoreSource,
)


class FakeScoreSource:
    def __init__(
        self,
        scores: Optional[list[UpstreamScore]] = None,
        reauth_required: bool = False,
        upstream_error: Optional[tuple[int, str]] = None,
        on_fetch: Optional[Callable[[object], None]] = None,
    ):
        self.scores = list(scores) if scores is not None else []
        self.reauth_required = reauth_required
        self.upstream_error = upstream_error
        self.on_fetch = on_fetch
        self.calls = 0

    def fetch_scores(self, user) -> list[UpstreamScore]:
        self.calls += 1
        if self.on_fetch is not None:
            self.on_fetch(user)
        if self.reauth_required:
            raise ReauthRequired()
        if self.upstream_error is not None:
            status, body = self.upstream_error
            raise UpstreamError(status=status, body=body)
        return self.scores
