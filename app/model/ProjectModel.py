import asyncio
from decimal import Decimal

from pydantic import computed_field
from sqlalchemy.orm import aliased
from sqlmodel import Field, select, Relationship, func

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDecimal
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


  @classmethod
  async def query_stats(
    cls,
    order_by: str = "name",
    order_dir: str = "asc",
    session = None
  ):
    """
    查询项目统计信息，支持排序

    Args:
        order_by: 排序字段，可选值: name, leader_name, spent, balance
        order_dir: 排序方向，可选值: asc, desc
        session: 可选的数据库会话，如果不传则自动创建
    """
    from app.model.UserModel import PrivateUserModel
    from app.model.ApproveModel import ApproveModel

    # 1. 创建子查询：统计每个项目已批准的总花费
    approve_subq = (
      select(
        ApproveModel.proj_id,
        func.coalesce(func.sum(ApproveModel.amount), 0).label("spent")
      )
      .where(ApproveModel.status == "approved")
      .group_by(ApproveModel.proj_id)
      .subquery()
    )

    # 2. 构建主查询
    spent_subq = aliased(approve_subq, name="spent_subq")

    # 定义查询字段 - 可以根据需要选择返回哪些字段
    query = (
      select(
        cls,
        PrivateUserModel.full_name.label("leader_name"),
        func.coalesce(spent_subq.c.spent, 0).label("spent"),
        (cls.budget - func.coalesce(spent_subq.c.spent, 0)).label("balance")
      )
      .outerjoin(PrivateUserModel, cls.leader_id == PrivateUserModel.id)
      .outerjoin(spent_subq, cls.id == spent_subq.c.proj_id)
    )

    # 3. 处理排序
    order_field_map = {
      "name": cls.name,
      "leader_name": PrivateUserModel.full_name,
      "spent": func.coalesce(spent_subq.c.spent, 0),
      "balance": (cls.budget - func.coalesce(spent_subq.c.spent, 0)),
      "budget": cls.budget
    }

    sort_field = order_field_map.get(order_by, cls.name)

    if order_dir.lower() == "desc":
      query = query.order_by(sort_field.desc())
    else:
      query = query.order_by(sort_field.asc())

    # 4. 执行查询
    if session:
      results = await session.execute(query)
    else:
      async with async_session() as sess:
        results = await sess.execute(query)

    # 5. 处理结果
    rows = results.all()

    project_stats = []
    for row in rows:
      project = row[0]
      # 动态设置计算字段到对象上（可选）
      project.__dict__["_leader_name"] = row[1]
      project.__dict__["_spent"] = Decimal(str(row[2])) if row[2] is not None else Decimal(0)
      project.__dict__["_balance"] = Decimal(str(row[3])) if row[3] is not None else None

      project_stats.append({
        "project": project,
        "leader_name": row[1],
        "spent": Decimal(str(row[2])) if row[2] is not None else Decimal(0),
        "balance": Decimal(str(row[3])) if row[3] is not None else None
      })

    return project_stats


if __name__ == "__main__":
  async def main():
    from app.model.UserModel import PrivateUserModel
    from app.model.ApproveModel import ApproveModel

    # 测试新的统计查询方法
    print("=== 测试统计查询（按余额降序） ===")
    stats = await ProjectModel.query_stats(order_by="balance", order_dir="desc")
    for stat in stats:
      print(f"项目: {stat['project'].name}, "
            f"负责人: {stat['leader_name']}, "
            f"预算: {stat['project'].budget}, "
            f"已花费: {stat['spent']}, "
            f"余额: {stat['balance']}")


  asyncio.run(main())
