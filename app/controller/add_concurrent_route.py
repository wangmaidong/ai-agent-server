import asyncio
from decimal import Decimal

import httpx
import uvicorn
from sqlmodel import select
from starlette import status

from app.model.BasicModel import BasicModel
from fastapi import FastAPI, HTTPException
from pydantic import Field

from app.model.LlmDemoModel import LlmDemoModel
from app.utils.model_utils import FormattedDecimal
from app.utils.mysql_utils import AsyncSessionDep


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


if __name__ == '__main__':
  async def main():
    recharge_url = 'http://127.0.0.1:7004/llm_demo/recharge'
    async with httpx.AsyncClient(timeout=30.0) as http_client:
      results = await asyncio.gather(
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 10})),
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 20})),
        asyncio.create_task(http_client.post(recharge_url, json={'id': '001', 'amount': 30})),
      )
      for item in results:
        obj = LlmDemoModel.to_obj(item.json().get('result'))
        print(obj.full_name, obj.amount)


  asyncio.run(main())
