from app.batis.batis_interceptors.BatisInterceptorManager import batis_aop
from app.model.ModuleModel import module_cache


# 修改用户信息之后，刷新用户信息中的缓存
def add_interceptor_module():
  @batis_aop(module="module", action=["after_insert", "after_update"])
  async def refresh_row(row: dict):
    if row['code']:
      await module_cache.refresh_cache(row['code'])

  @batis_aop(module="module", action=["after_batch_insert", "after_batch_update"])
  async def refresh_row_list(rows: list[dict]):
    for row in rows:
      if row['code']:
        await module_cache.refresh_cache(row['code'])

  @batis_aop(module="module", action=["before_delete"])
  async def before_row_delete(delete_body, session):
    # 在删除前先查询出数据，获取 code 以便删除缓存
    item_ids = delete_body.id if isinstance(delete_body.id, list) else [delete_body.id]
    await module_cache.remove_cache_by_id(item_ids)
