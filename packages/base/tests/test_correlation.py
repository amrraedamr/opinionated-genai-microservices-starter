"""Correlation identity adoption and propagation."""

from uuid import uuid4

from base.tools import correlation


class TestAdopt:
    def test_adopts_an_inbound_uuid(self):
        incoming = uuid4()
        assert correlation.adopt(str(incoming)) == incoming

    def test_adopts_a_w3c_traceparent(self):
        trace = uuid4().hex
        header = f"00-{trace}-0123456789abcdef-01"
        assert correlation.adopt(None, header).hex == trace

    def test_generates_one_when_absent(self):
        assert correlation.adopt(None, None) is not None

    def test_ignores_a_malformed_value(self):
        generated = correlation.adopt("not-a-correlation-id")
        assert generated is not None

    def test_current_returns_the_adopted_value(self):
        incoming = uuid4()
        correlation.adopt(str(incoming))
        assert correlation.current() == incoming
