import asyncio
from decimal import Decimal

import httpx
import uvicorn
from sqlalchemy import update, and_
from sqlmodel import select
from starlette import status

from app.model.BasicModel import BasicModel
from fastapi import FastAPI, HTTPException
from pydantic import Field

from app.model.LlmDemoModel import LlmDemoModel
from app.utils.model_utils import FormattedDecimal
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.redis_utils import redis_utils
from app.utils.redis_lock import get_redis_lock

def add_concurrent_route(app: FastAPI):
  class DemoRechargeBodyScheme(BasicModel):
    id: str = Field(..., description="充值的记录的ID")
    amount: FormattedDecimal = Field(..., description="充值的金额")

  @app.post('/llm_demo/recharge')
  async def _recharge(body: DemoRechargeBodyScheme, session: AsyncSessionDep):
    async with session.begin():
      # 使用 FOR UPDATE 悲观锁
      query = (select(LlmDemoModel).where(LlmDemoModel.id == body.id)).with_for_update()
      result = await session.execute(query)
      obj = result.scalars().first()

      if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="充值的记录不存在", )

      obj.amount = obj.amount + body.amount
      session.add(obj)

    return {"result": obj}

  @app.post('/llm_demo/recharge/positive')
  async def _recharge(body: DemoRechargeBodyScheme, session: AsyncSessionDep):
    max_retries = 3

    for i in range(max_retries):
      # 开启一个子事务（或者在循环外开启大事务，失败时回滚到 savepoint）
      # 这里演示最稳妥的：每次重试都是一个独立的逻辑事务单元
      print(f"retry ==>> {i}, {body.amount}")
      try:
        async with session.begin():  # 自动开启事务
          # 1. 查询当前版本
          query = select(LlmDemoModel).where(LlmDemoModel.id == body.id)
          result = await session.execute(query)
          obj = result.scalars().first()

          if not obj:
            raise HTTPException(status_code=404, detail="记录不存在")

          current_version = obj.version

          # 2. 尝试更新
          # 注意：必须在 WHERE 中加入 version 校验
          stmt = (
            update(LlmDemoModel)
            .where(and_(LlmDemoModel.id == body.id, LlmDemoModel.version == current_version))
            .values(
              amount=obj.amount + body.amount,
              version=(current_version or 0) + 1
            )
          )

          update_result = await session.execute(stmt)
          await session.refresh(obj)

          # 3. 检查是否更新成功
          if update_result.rowcount > 0:
            # 提交事务并返回
            # session.begin() 块结束时会自动 commit
            return {"result": obj, "body_amount": body.amount}

          # 如果 rowcount == 0，说明版本已被修改，手动抛出异常触发 rollback
          raise Exception("Version Conflict")

      except Exception as e:
        # 如果是版本冲突，则继续下一次重试
        if str(e) == "Version Conflict":
          if i == max_retries - 1:
            raise HTTPException(status_code=409, detail="系统繁忙，并发冲突")
          continue
          # 其他异常则直接抛出
        raise e
    raise HTTPException(status_code=409, detail="系统繁忙，并发冲突")

  @app.post('/llm_demo/recharge/atomic')
  async def _recharge_atomic(body: DemoRechargeBodyScheme, session: AsyncSessionDep):
    # 1. 构造原子更新语句
    # 直接在数据库执行: SET amount = amount + :val
    stmt = (
      update(LlmDemoModel)
      .where(LlmDemoModel.id == body.id)
      .values(amount=LlmDemoModel.amount + body.amount)
    )

    # 2. 执行更新
    result = await session.execute(stmt)

    # 3. 检查记录是否存在
    if result.rowcount == 0:
      raise HTTPException(status_code=404, detail="充值的记录不存在")

    # 4. (可选) 如果需要返回更新后的结果，需要重新查询一次
    # 因为 update 语句本身不返回修改后的对象实体
    query = select(LlmDemoModel).where(LlmDemoModel.id == body.id)
    updated_obj = (await session.execute(query)).scalars().first()

    # 没开启事务，需要手动提交
    await session.commit()

    return {"result": updated_obj, "body_amount": body.amount}

  # /*---------------------------------------分布式锁-------------------------------------------*/
  @app.post('/llm_demo/recharge/redis_lock')
  async def _recharge(body: DemoRechargeBodyScheme, session: AsyncSessionDep):
    # 1. 定义锁的 Key，通常以业务逻辑 + ID 命名
    lock_key = f"lock:recharge:{body.id}"

    # 获取 redis 客户端（假设你已经有工具类获取 redis_client）
    async with redis_utils.get_redis_connection() as redis_client:
      try:
        # 2. 使用你写的分布式锁
        async with get_redis_lock(lock_key, redis_client, timeout=10, acquire_timeout=5):
          # --- 核心业务逻辑开始 ---
          # 此时已经拿到了锁，同一时间只有一个进程/协程能进入这里
          async with session.begin():
            query = select(LlmDemoModel).where(LlmDemoModel.id == body.id)
            result = await session.execute(query)
            obj = result.scalars().first()

            if not obj:
              raise HTTPException(status_code=404, detail="记录不存在")

            obj.amount += body.amount
            session.add(obj)
          # --- 核心业务逻辑结束 ---

          return {"result": obj, "body_amount": body.amount}

      except TimeoutError:
        # 获取锁超时（竞争太激烈）
        raise HTTPException(status_code=429, detail="系统繁忙，请稍后再试")


if __name__ == '__main__':
  async def main():
    recharge_url = 'http://127.0.0.1:7004/llm_demo/recharge/redis_lock'
    async with httpx.AsyncClient(timeout=30.0) as http_client:
      results = await asyncio.gather(
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 10})),
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 20})),
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 30})),
      )
      for item in results:
        json_data = item.json()
        body_amount = json_data.get("body_amount")
        obj = LlmDemoModel.to_obj(json_data.get('result'))
        print(body_amount, obj.amount)


  asyncio.run(main())
