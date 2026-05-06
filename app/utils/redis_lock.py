import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from app.utils.redis_utils import redis_utils
from redis.asyncio import Redis

# 用于释放锁的 Lua 脚本（保证原子性：匹配 token 再删除）
# Lua 脚本在 Redis 中执行时是原子性的。Redis 会保证整个脚本在执行期间，不会有其他命令插入进来。
RELEASE_LUA_SCRIPT = """
-- KEYS[1] 是 lock_key
-- ARGV[1] 是我们持有的 token (uuid)

-- 1. 取出当前 Redis 里存的 token
if redis.call("get", KEYS[1]) == ARGV[1] then
    -- 2. 如果值相等，说明这把锁还是我的，可以安全删除
    return redis.call("del", KEYS[1])
else
    -- 3. 如果值不相等，说明锁已经过期被别人占领了，我什么都不做
    return 0
end
"""


@asynccontextmanager
async def get_redis_lock(
  lock_key: str,
  redis_client: Redis,
  timeout: int = 10,
  acquire_timeout: int = 30,
  retry_interval: float = 0.1
):
  """
  Redis 分布式锁异步上下文管理器

  :param lock_key: 锁的键名
  :param redis_client: redis-py 的异步客户端
  :param timeout: 锁的超时时间（秒），防止死锁，默认 10 秒
  :param acquire_timeout: 获取锁的超时时间（秒），避免无限等待，默认 30 秒
  :param retry_interval: 获取失败时的重试频率（秒），默认 0.1 秒
  :raises TimeoutError: 当获取锁超时时抛出
  """
  token = str(uuid.uuid4())  # 唯一标识，防止误释放
  start_time = time.time()

  try:
    # 循环尝试获取锁（自旋）
    while True:
      # nx=True: 只在键不存在时设置; ex=timeout: 设置过期时间
      acquired = await redis_client.set(lock_key, token, nx=True, ex=timeout)
      if acquired:
        break

      # 检查是否超过获取锁的超时时间
      if time.time() - start_time > acquire_timeout:
        raise TimeoutError(f"Failed to acquire lock {lock_key} within {acquire_timeout} seconds")

      await asyncio.sleep(retry_interval)

    yield token  # 获取锁成功，执行业务逻辑

  finally:
    # 无论业务逻辑是否报错，都尝试释放锁
    # 使用 Lua 脚本确保只删除自己持有的那把锁
    # 如果锁是自己的，就释放掉；
    # 如果因为锁过期被别人占用了，则什么事也不做；
    await redis_client.eval(RELEASE_LUA_SCRIPT, 1, lock_key, token)


if __name__ == "__main__":
  async def main():
    async def acquire_lock(lock_name, lock_token):
      # 获取锁的超时时间
      acquire_timeout = 3
      # 锁的超时时间
      lock_timeout = 10
      # 开始时间
      start_time = time.time()

      while True:
        # 尝试拿锁
        acquired = await redis_client.set(lock_name, lock_token, nx=True, ex=lock_timeout)
        if acquired:
          break
        if time.time() - start_time > acquire_timeout:
          # 已经超时
          print(f"{lock_token} get lock failed with timeout: {acquire_timeout}")
          break
        # 没有超时，等待之后下一次循环继续尝试拿锁
        await asyncio.sleep(0.1)

      return acquired, lock_name, lock_token

    async def release_lock(lock_name, lock_token):
      await redis_client.eval(RELEASE_LUA_SCRIPT, 1, lock_name, lock_token)

    # 任务的执行过程，打印开始、获得锁、结束日志；
    async def job(lock_name, lock_token, job_duration: int):
      print(lock_token, "begin", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      acquire, lock_name, lock_token = await acquire_lock(lock_name, lock_token)
      print(lock_token, f"getLock {'success' if acquire else 'failed'}!", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await asyncio.sleep(job_duration)
      await release_lock(lock_name, lock_token)
      print(lock_token, "end", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      return acquire, lock_name, lock_token

    async with redis_utils.get_redis_connection() as redis_client:
      result = await asyncio.gather(
        asyncio.create_task(job('lock:张三', "A", 1)),
        asyncio.create_task(job('lock:张三', "B", 2)),
        asyncio.create_task(job('lock:张三', "C", 3)),
      )
      for item in result:
        print(item)


  asyncio.run(main())
