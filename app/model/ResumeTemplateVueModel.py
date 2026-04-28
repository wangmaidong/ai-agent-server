from sqlmodel import Field

from app.model.BasicModel import BasicModel
from app.utils.model_utils import FormattedDatetime, FormattedDate, FormattedDecimal


class ResumeTemplateVueModel(BasicModel, table=True):
  __tablename__ = "llm_resume_template_vue"

  source_code: str | None = Field(default=None, description="简历模板TSX代码")
  thumb_image: str | None = Field(default=None, description="简历模板缩略图")
  default_primary: str | None = Field(default=None, description="默认主题色")
  default_secondary: str | None = Field(default=None, description="默认次级色")
