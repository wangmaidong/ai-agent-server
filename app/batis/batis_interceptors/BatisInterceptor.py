from app.batis.batis_interceptors.batis_func_types import BeforeList, AfterList, BeforeInsert, AfterInsert, BeforeUpdate, AfterUpdate, BeforeBatchInsert, AfterBatchInsert, BeforeBatchUpdate, AfterBatchUpdate, BeforeDelete, AfterDelete


class BatisInterceptor:
  def __init__(
    self,
    module: str,
    before_list: BeforeList | None = None,
    after_list: AfterList | None = None,
    before_insert: BeforeInsert | None = None,
    after_insert: AfterInsert | None = None,
    before_update: BeforeUpdate | None = None,
    after_update: AfterUpdate | None = None,
    before_batch_insert: BeforeBatchInsert | None = None,
    after_batch_insert: AfterBatchInsert | None = None,
    before_batch_update: BeforeBatchUpdate | None = None,
    after_batch_update: AfterBatchUpdate | None = None,
    before_delete: BeforeDelete | None = None,
    after_delete: AfterDelete | None = None,
  ):
    self.module = module
    self.before_list = before_list
    self.after_list = after_list
    self.before_insert = before_insert
    self.after_insert = after_insert
    self.before_update = before_update
    self.after_update = after_update
    self.before_batch_insert = before_batch_insert
    self.after_batch_insert = after_batch_insert
    self.before_batch_update = before_batch_update
    self.after_batch_update = after_batch_update
    self.before_delete = before_delete
    self.after_delete = after_delete
