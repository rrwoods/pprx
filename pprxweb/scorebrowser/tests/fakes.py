from typing import Optional
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
    ):
        self.scores = list(scores) if scores is not None else []
        self.reauth_required = reauth_required
        self.upstream_error = upstream_error

    def fetch_scores(self, user) -> list[UpstreamScore]:
        if self.reauth_required:
            raise ReauthRequired()
        if self.upstream_error is not None:
            status, body = self.upstream_error
            raise UpstreamError(status=status, body=body)
        return self.scores
