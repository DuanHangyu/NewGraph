"""
AsyncBridge - asyncio 后台线程桥接

Graphiti SDK 是全 async 的，Flask 是 sync 的。
通过单例后台线程运行持久事件循环来桥接两者，
避免每次请求创建/销毁事件循环。
"""

import asyncio
import threading
import logging
from typing import TypeVar, Coroutine
from concurrent.futures import Future

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncBridge:
    """单例 asyncio 后台线程桥接器"""

    _loop: asyncio.AbstractEventLoop | None = None
    _thread: threading.Thread | None = None
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """启动后台线程和事件循环"""
        if cls._initialized:
            return

        cls._loop = asyncio.new_event_loop()

        def _run_loop():
            asyncio.set_event_loop(cls._loop)
            cls._loop.run_forever()

        cls._thread = threading.Thread(target=_run_loop, daemon=True, name="async-bridge")
        cls._thread.start()
        cls._initialized = True
        logger.info("AsyncBridge 已启动")

    @classmethod
    def run(cls, coro: Coroutine[..., ..., T]) -> T:
        """
        在后台事件循环中运行协程，同步等待结果。

        用法:
            result = AsyncBridge.run(some_async_function(arg1, arg2))
        """
        if not cls._initialized or cls._loop is None:
            raise RuntimeError("AsyncBridge 未初始化，请先调用 AsyncBridge.initialize()")

        future: Future[T] = asyncio.run_coroutine_threadsafe(coro, cls._loop)
        return future.result()

    @classmethod
    def shutdown(cls) -> None:
        """安全关闭事件循环"""
        if not cls._initialized or cls._loop is None:
            return

        cls._loop.call_soon_threadsafe(cls._loop.stop)

        if cls._thread is not None:
            cls._thread.join(timeout=5)

        cls._initialized = False
        cls._loop = None
        cls._thread = None
        logger.info("AsyncBridge 已关闭")
