from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from src.database import Base

organization_activities = Table(
    "organization_activities",
    Base.metadata,
    Column("organization_id", ForeignKey("organizations.id"), primary_key=True),
    Column("activity_id", ForeignKey("activities.id"), primary_key=True),
)


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organizations = relationship("Organization", back_populates="building")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # self-relation для дерева
    children = relationship("Activity", backref="parent", remote_side=[id])


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_numbers = Column(String)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    building = relationship("Building", back_populates="organizations")
    activities = relationship(
        "Activity", secondary=organization_activities, backref="organizations"
    )
