from typing import Protocol, Optional

from app.batis.batis_utils.batis_scheme import BatisQueryBody, BatisDeleteBody
from app.model.UserModel import PublicUser
from app.utils.mysql_utils import AsyncSessionDep


class BeforeList(Protocol):
  def __call__(
    self,
    query_body: BatisQueryBody,
    session: AsyncSessionDep,
    user: Optional[PublicUser] = None
  ) -> None:
    pass


class AfterList(Protocol):
  def __call__(
    self,
    rows: list[dict],
    session: AsyncSessionDep,
    user: Optional[PublicUser] = None
  ) -> None:
    pass


class BeforeUpsert(Protocol):
  def __call__(
    self,
    row: dict,
    session: AsyncSessionDep,
    user: Optional[PublicUser] = None
  ) -> None:
    pass


BeforeInsert = BeforeUpsert
AfterInsert = BeforeUpsert
BeforeUpdate = BeforeUpsert
AfterUpdate = BeforeUpsert

BeforeBatchInsert = AfterList
AfterBatchInsert = AfterList
BeforeBatchUpdate = AfterList
AfterBatchUpdate = AfterList


class BeforeDelete(Protocol):
  def __call__(
    self,
    delete_body: BatisDeleteBody,
    session: AsyncSessionDep,
    user: Optional[PublicUser] = None
  ) -> None:
    pass


AfterDelete = BeforeDelete
