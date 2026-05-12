from decimal import Decimal

from pydantic import computed_field
from sqlmodel import Field, Relationship

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDecimal


class ApproveModel(BasicModel, table=True):
  __tablename__ = "pl_approve"

  title: str | None = Field(default=None, description="审批标题")
  description: str | None = Field(default=None, description="审批描述信息")
  status: str | None = Field(default=None, description="审批状态")
  amount: FormattedDecimal | None = Field(default=Decimal(0), description="审批金额")
  # proj_id: str | None = Field(default=None, description="所属项目id")
  user_id: str | None = Field(default=None, description="当前审批人id")
  logs: str | None = Field(default=None, description="审批日志")
  approve_from: str | None = Field(default=None, description="审批单来源类型")
  apply_user_id: str | None = Field(default=None, description="申请人的id")
  llm_flag: str | None = Field(default=None, description="LLM审核结果标识")
  llm_reason: str | None = Field(default=None, description="LLM审核不通过原因")

  # 1. 明确指向 pl_user 表的 id 字段
  proj_id: str | None = Field(
    default=None,
    foreign_key="pl_project.id",  # 假设 BasicModel 里的主键叫 id
    description="项目id"
  )

  # 2. 定义 Relationship，SQLModel 会自动根据 foreign_key 关联
  # project: "ProjectModel" = Relationship(back_populates="approve_list")

  # @computed_field
  # @property
  # def proj_name(self) -> str | None:
  #   return self.project.name if self.project else None
