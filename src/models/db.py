from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Launchpad(Base):
    __tablename__ = "launchpads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    locality: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    launch_attempts: Mapped[int] = mapped_column(Integer, default=0)
    launch_successes: Mapped[int] = mapped_column(Integer, default=0)

    launches: Mapped[list["Launch"]] = relationship(back_populates="launchpad")


class Core(Base):
    __tablename__ = "cores"

    serial: Mapped[str] = mapped_column(String, primary_key=True)
    reuse_count: Mapped[int] = mapped_column(Integer, default=0)
    rtls_attempts: Mapped[int] = mapped_column(Integer, default=0)
    rtls_landings: Mapped[int] = mapped_column(Integer, default=0)
    asds_attempts: Mapped[int] = mapped_column(Integer, default=0)
    asds_landings: Mapped[int] = mapped_column(Integer, default=0)

    launch_cores: Mapped[list["LaunchCore"]] = relationship(back_populates="core")


class Launch(Base):
    __tablename__ = "launches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    flight_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    date_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    rocket_id: Mapped[str] = mapped_column(String, nullable=False)
    launchpad_id: Mapped[str | None] = mapped_column(String, ForeignKey("launchpads.id"), nullable=True)

    launchpad: Mapped["Launchpad | None"] = relationship(back_populates="launches")
    launch_cores: Mapped[list["LaunchCore"]] = relationship(back_populates="launch")


class LaunchCore(Base):
    __tablename__ = "launch_cores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    launch_id: Mapped[str] = mapped_column(String, ForeignKey("launches.id"), index=True)
    core_serial: Mapped[str | None] = mapped_column(String, ForeignKey("cores.serial"), nullable=True)
    flight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gridfins: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    legs: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reused: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    landing_attempt: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    landing_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    landing_type: Mapped[str | None] = mapped_column(String, nullable=True)

    launch: Mapped["Launch"] = relationship(back_populates="launch_cores")
    core: Mapped["Core | None"] = relationship(back_populates="launch_cores")
