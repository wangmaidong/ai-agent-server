import asyncio
from decimal import Decimal

from pydantic import computed_field
from sqlmodel import Field, select, Relationship

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDatetime, FormattedDate, FormattedDecimal
from app.utils.mysql_utils import async_session


class ProjectModel(BasicModel, table=True):
  __tablename__ = "pl_project"

  name: str | None = Field(default=None, description="项目名称")
  description: str | None = Field(default=None, description="项目描述")
  budget: FormattedDecimal = Field(default=Decimal(0), description="项目预算金额")

  # 1. 明确指向 pl_user 表的 id 字段
  leader_id: str | None = Field(
    default=None,
    foreign_key="pl_user.id",  # 假设 BasicModel 里的主键叫 id
    description="项目负责人id"
  )

  # 2. 定义 Relationship，SQLModel 会自动根据 foreign_key 关联
  leader: "PrivateUserModel" = Relationship(back_populates="projects")

  @computed_field
  @property
  def leader_name(self) -> str | None:
    return self.leader.full_name if self.leader else None


if __name__ == "__main__":
  async def main():
    from app.model.UserModel import PrivateUserModel

    async with async_session() as session:
      from sqlalchemy.orm import joinedload

      # --- 修改 1: 查询项目关联负责人 ---
      results = await session.execute(
        select(ProjectModel).options(joinedload(ProjectModel.leader))
      )
      # 虽然一对一通常不需要，但养成习惯加上 .unique() 更稳健
      projects = results.unique().scalars().all()
      for project in projects:
        print(project.to_dict())

      # --- 修改 2: 查询用户关联项目 (报错发生的点) ---
      results = await session.execute(
        select(PrivateUserModel).options(joinedload(PrivateUserModel.projects))
      )
      # 关键点：必须调用 .unique()
      users = results.unique().scalars().all()

      for user in users:
        print(f"---------------{user.full_name}-------------------")
        for project in user.projects:
          print(project.id, project.name, project.budget)


  asyncio.run(main())
