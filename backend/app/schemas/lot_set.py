from datetime import datetime

from app.schemas.common import ApiModel


class LotSetOut(ApiModel):
    id: int
    name: str
    uploaded_at: datetime
    lots_count: int
    is_active: bool


class FeedUploadResult(ApiModel):
    set: LotSetOut
    skipped: int  # лоты фида, не прошедшие разбор
