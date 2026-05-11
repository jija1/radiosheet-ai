from sqlalchemy import Column, Integer, String, Text

from app.db.session import Base


class RunSheetRecord(Base):
    __tablename__ = "runsheet_records"

    id                    = Column(String,  primary_key=True)
    programme_type        = Column(String,  nullable=False)
    station_name          = Column(String,  nullable=False)
    presenter_name        = Column(String,  nullable=False)
    total_duration_minutes = Column(Integer, nullable=False)
    segments_json         = Column(Text,    nullable=False)
    conflicts_json        = Column(Text,    nullable=False)
    recommendations_json  = Column(Text,    nullable=False)
    stats_json            = Column(Text,    nullable=False)
    programme_input_json  = Column(Text,    nullable=False)
    generated_at          = Column(String,  nullable=False)
