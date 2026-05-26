from app.batis.batis_interceptors.BatisInterceptorManager import batis_aop
from app.model.UserModel import user_cache


# 修改用户信息之后，刷新用户信息中的缓存
def add_add_interceptor_user():
  @batis_aop(module="user", action=["after_insert", "after_update"])
  async def refresh_user_cache(row: dict):
    await user_cache.refresh_cache(row['username'])

  @batis_aop(module="user", action=["after_batch_insert", "after_batch_update"])
  async def refresh_user_cache_list(rows: list[dict]):
    for row in rows:
      await user_cache.refresh_cache(row['username'])

  @batis_aop(module="user", action=["before_delete"])
  async def before_user_delete(delete_body, session):
    # 在删除前先查询出数据，获取 username 以便删除缓存
    item_ids = delete_body.id if isinstance(delete_body.id, list) else [delete_body.id]
    await user_cache.remove_cache_by_id(item_ids)

if __name__ == "__main__":
  from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager

  add_add_interceptor_user()
  print(batis_interceptor_manager.interceptors)
