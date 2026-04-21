import uuid
from decimal import Decimal
from typing import List

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Field, select

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDatetime, FormattedDate, FormattedDecimal
from app.utils.mysql_utils import AsyncSessionDep


class LlmDemoModel(BasicModel, table=True):
  __tablename__ = "llm_demo"

  full_name: str | None = Field(default=None, description="用户名称")
  datetime_start: FormattedDatetime | None = Field(default=None, description="开通会员时间")
  datetime_end: FormattedDatetime | None = Field(default=None, description="会员截止到期时间")
  birthday: FormattedDate | None = Field(default=None, description="生日")
  amount: FormattedDecimal | None = Field(default=Decimal(0), description="金额")
