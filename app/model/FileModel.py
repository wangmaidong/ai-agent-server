import datetime
from pathlib import Path
from typing import Optional, Callable, Awaitable

import aiofiles
from anyio._core._fileio import ReadableBuffer
from fastapi import UploadFile
from sqlmodel import Field

from app.config.env import env
from app.model.BasicModel import BasicModel
from app.utils.model_utils import to_obj
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.next_id import next_id
from app.utils.path_join import path_join


class FileModel(BasicModel, table=True):
  __tablename__ = "pl_upload"

  name: str | None = Field(default=None, description='文件名称')
  path: str | None = Field(default=None, description='文件路径')
  head_id: str | None = Field(default=None, description='父对象id')
  attr1: str | None = Field(default=None, description='扩展属性1')
  attr2: str | None = Field(default=None, description='扩展属性2')
  attr3: str | None = Field(default=None, description='扩展属性3')
  content: str | None = Field(default=None, description='扩展属性内容文本')


# 文件保存服务
class FileSaveService:
  # 将文件保存到服务本地目录
  # 并且往附件表中插入对应的文件记录
  @staticmethod
  async def saveFile(
    session: AsyncSessionDep,
    file: UploadFile,
    filename: str,
    id: str = None,
    file_record: dict = None,
  ):
    file_cls = await async_save_file(
      filename=filename,
      session=session,
      aget_file_blob=file.read,
      id=id,
      file_record=file_record,
    )
    return {"result": file_cls.model_dump()}


async def async_save_file(
  # 保存的文件名
  filename: str,
  # 数据库会话管理对象
  session: AsyncSessionDep,
  # 异步获取文件buffer的方法
  aget_file_blob: Callable[[], Awaitable[ReadableBuffer]],
  # 文件id，没有则自动生成
  id: str | None = None,
  # 其他额外的要保存附件记录中的字段信息
  file_record: dict | None = None,
):
  """
  保存文件工具函数
  """

  if not id:
    id = await next_id()

  datetime_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
  file_id = f"{datetime_string}_{id}"

  # 文件的保存路径，用来将文件写入到磁盘
  # save_path=/www/wwwroot/web/web/upload_file/时间+随机ID
  save_path = path_join(env.server_file_save_path, file_id)
  print("save_path", save_path)

  # 文件的访问路径，用来生成文件的访问路径，然后存到附件表中的path字段中
  # public_path=/web/upload_file/时间+随机ID
  public_path = path_join(env.server_file_public_path, file_id)
  print("public_path", public_path)

  # parents=True 表示创建所有不存在的父目录
  # exist_ok=True 表示如果目录已存在不抛出异常
  Path(save_path).mkdir(parents=True, exist_ok=True)

  file_save_path = path_join(save_path, filename)  # 文件的保存路径
  file_public_path = path_join(public_path, filename)  # 文件的访问路径

  # with open(file_save_path, 'wb') as f:
  #   f.write(await file.read())
  file_blob = await aget_file_blob()
  async with aiofiles.open(file_save_path, 'wb') as f:
    await f.write(file_blob)
    await f.flush()  # 确保数据写入磁盘

  file_dict = {
    "id": id,
    "name": filename,
    "path": file_public_path,
    **file_record,
  }
  new_file_obj = to_obj(FileModel, file_dict)
  session.add(new_file_obj)
  await session.commit()
  return new_file_obj


def get_file_record_save_path(file_record_path: str):
  """
  获取文件的保存路径
  """
  return env.file_save_path + file_record_path[len(env.file_public_path):]
