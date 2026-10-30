"""Tests for AsyncLoopManager and async event loop stability."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.telegram_client import get_async_loop_manager


def test_async_loop_manager_singleton():
    mgr1 = get_async_loop_manager()
    mgr2 = get_async_loop_manager()
    assert mgr1 is mgr2
    assert mgr1.loop.is_running()


def test_async_loop_manager_run_coro_sync():
    mgr = get_async_loop_manager()

    async def add(a, b):
        await asyncio.sleep(0.01)
        return a + b

    res = mgr.run_coro_sync(add(10, 20), timeout=2)
    assert res == 30


def test_sequential_calls_use_same_loop():
    mgr = get_async_loop_manager()
    loops = []

    async def record_loop():
        loop = asyncio.get_running_loop()
        loops.append(loop)
        return loop

    loop1 = mgr.run_coro_sync(record_loop(), timeout=2)
    loop2 = mgr.run_coro_sync(record_loop(), timeout=2)

    assert loop1 is loop2
    assert loop1 is mgr.loop
