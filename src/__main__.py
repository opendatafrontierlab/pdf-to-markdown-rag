import asyncio

from . import threads  # noqa: F401  (must run before heavy native imports)
from .main import main

asyncio.run(main())
