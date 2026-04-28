from sqlmodel import Field

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDatetime, FormattedDate, FormattedDecimal


class ResumeUserVueModel(BasicModel, table=True):
  __tablename__ = "llm_resume_user_vue"

  source_code: str | None = Field(default=None, description="简历模板TSX代码")
  thumb_image: str | None = Field(default=None, description="简历模板缩略图")
  resume_json_string: str | None = Field(default=None, description="简历模板JSON数据")
