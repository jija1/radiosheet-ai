from sqlalchemy import Boolean, Column, Integer, String

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(String, primary_key=True)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(String, nullable=False)
    last_login      = Column(String, nullable=True)
    display_name    = Column(String(100), nullable=True)

    # User preferences (Settings page — Part 7)
    default_station_name        = Column(String(100), nullable=True)
    default_presenter_name      = Column(String(100), nullable=True)
    default_programme_type      = Column(String(50),  nullable=True)
    default_duration_minutes    = Column(Integer,      nullable=True)
    default_talk_music_preference = Column(String(20), nullable=True)
    default_max_adverts_per_hour  = Column(Integer,    nullable=True)
    time_format                 = Column(String(3),    nullable=False, default="24h")
    cultural_calendar_enabled   = Column(Boolean,      nullable=False, default=True)
    strict_mode                 = Column(Boolean,      nullable=False, default=False)
    auto_apply_fixes            = Column(Boolean,      nullable=False, default=False)
    notifications_enabled       = Column(Boolean,      nullable=False, default=True)
    default_region              = Column(String(30),   nullable=True)
    station_audience            = Column(String(10),   nullable=True)
    recommendation_depth        = Column(String(10),   nullable=False, default="standard")
