"""Unit tests for circuit breaker."""
import pytest
import asyncio
from app.services.api_clients.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=1  # 1 second for testing
        )

    @pytest.mark.asyncio
    async def test_circuit_closed_on_success(self):
        """Test circuit remains closed on successful calls."""
        async def successful_call():
            return "success"

        result = await self.circuit_breaker.call(successful_call)
        assert result == "success"
        assert self.circuit_breaker.state == "CLOSED"
        assert self.circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after reaching failure threshold."""
        async def failing_call():
            raise Exception("API error")

        # First 3 failures should trigger circuit open
        for i in range(3):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_call)

        assert self.circuit_breaker.state == "OPEN"
        assert self.circuit_breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_rejects_calls_when_open(self):
        """Test circuit breaker rejects calls when open."""
        async def failing_call():
            raise Exception("API error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_call)

        # Next call should be rejected immediately
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await self.circuit_breaker.call(failing_call)

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        async def failing_call():
            raise Exception("API error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_call)

        assert self.circuit_breaker.state == "OPEN"

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Should transition to HALF_OPEN
        async def successful_call():
            return "recovered"

        result = await self.circuit_breaker.call(successful_call)
        assert result == "recovered"
        assert self.circuit_breaker.state == "CLOSED"  # Closed after successful half-open call
        assert self.circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_reopens_on_half_open_failure(self):
        """Test circuit reopens if half-open call fails."""
        async def failing_call():
            raise Exception("API error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_call)

        # Wait for timeout to enter half-open
        await asyncio.sleep(1.1)

        # Fail in half-open state
        with pytest.raises(Exception):
            await self.circuit_breaker.call(failing_call)

        # Should return to OPEN
        assert self.circuit_breaker.state == "OPEN"

    @pytest.mark.asyncio
    async def test_failure_count_resets_on_success(self):
        """Test failure count resets after successful call."""
        async def failing_call():
            raise Exception("API error")

        async def successful_call():
            return "success"

        # Two failures (below threshold)
        for i in range(2):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_call)

        assert self.circuit_breaker.failure_count == 2

        # Successful call should reset count
        await self.circuit_breaker.call(successful_call)
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_custom_failure_threshold(self):
        """Test circuit breaker with custom threshold."""
        cb = CircuitBreaker(failure_threshold=5, timeout=1)

        async def failing_call():
            raise Exception("API error")

        # Should take 5 failures to open
        for i in range(4):
            with pytest.raises(Exception):
                await cb.call(failing_call)
            assert cb.state == "CLOSED"

        # Fifth failure opens circuit
        with pytest.raises(Exception):
            await cb.call(failing_call)
        assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_concurrent_calls_with_circuit_breaker(self):
        """Test circuit breaker handles concurrent calls correctly."""
        call_count = 0

        async def counting_call():
            nonlocal call_count
            call_count += 1
            return call_count

        # Multiple concurrent successful calls
        results = await asyncio.gather(*[
            self.circuit_breaker.call(counting_call)
            for _ in range(10)
        ])

        assert len(results) == 10
        assert self.circuit_breaker.state == "CLOSED"
        assert call_count == 10
