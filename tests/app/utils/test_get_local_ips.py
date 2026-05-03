import pytest

from app.utils.get_local_ips import get_local_ips


@pytest.mark.asyncio
async def test_get_local_ips():
  ips = get_local_ips()
  print(ips)
  assert len(ips) > 0
