from fastapi import FastAPI

from app.batis.add_batis_route import add_batis_route
from app.batis.batis_utils.batis_scheme import BatisModuleColumn, BatisValidRule
from app.model.LlmDemoModel import LlmDemoModel


def add_batis_demo_route(app: FastAPI):
  # /*---------------------------------------/batis_demo-------------------------------------------*/
  add_batis_route(app, clazz=LlmDemoModel, base="/batis_demo")

  # /*---------------------------------------/batis_demo_valid-------------------------------------------*/
  external_columns = {
    # full_name: 必填，最小长度2，最大长度20
    "fullName": BatisModuleColumn(
      value_type="string",
      rules=[
        BatisValidRule(type="string", required=True, message="用户名称为必填项"),
        BatisValidRule(type="string", min=2, message="用户名称长度不能少于2位"),
        BatisValidRule(type="string", max=20, message="用户名称长度不能超过20位"),
      ]
    ),
    # amount: 必填，最小值0，最大值1000000
    "amount": BatisModuleColumn(
      value_type="number",
      rules=[
        BatisValidRule(type="number", required=True, message="金额为必填项"),
        BatisValidRule(type="number", min=0, message="金额不能小于0"),
        BatisValidRule(type="number", max=1000000, message="金额不能超过1000000"),
      ]
    ),
    # version: 必填，枚举值只能是0,1,2
    "version": BatisModuleColumn(
      value_type="number",
      rules=[
        BatisValidRule(type="number", required=True, message="版本号为必填项"),
      ]
    ),
  }
  add_batis_route(app, clazz=LlmDemoModel, base="/batis_demo_valid", external_columns=external_columns)
