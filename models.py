"""Relational Sudana data model used by PostgreSQL and local migration tests."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id():
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    username: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    middle_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str] = mapped_column(String(80))
    display_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    gender: Mapped[str] = mapped_column(String(40))
    date_of_birth: Mapped[Date] = mapped_column(Date)
    hometown: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    home_country: Mapped[str | None] = mapped_column(String(160), nullable=True)
    is_south_sudanese: Mapped[bool] = mapped_column(Boolean, default=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="")
    photo_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class AccountState(Base):
    """Compatibility state used while existing routes move to normalized tables.

    This data lives inside PostgreSQL, not a local JSON file. It permits a safe,
    lossless rollout of the relational schema without rewriting every social
    workflow in one deployment.
    """
    __tablename__ = "account_states"
    user_key: Mapped[str] = mapped_column(String(120), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    media_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    author: Mapped[User] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    reactions: Mapped[list["Reaction"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PostShareTarget(Base):
    __tablename__ = "post_share_targets"
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    post: Mapped[Post] = relationship(back_populates="comments")


class Reaction(Base):
    __tablename__ = "reactions"
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    reaction_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    post: Mapped[Post] = relationship(back_populates="reactions")


class SharedPost(Base):
    __tablename__ = "shared_posts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    original_post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True)
    sharing_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    commentary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MyGRequest(Base):
    __tablename__ = "myg_requests"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("sender_id", "recipient_id", name="uq_myg_request_pair"),)


class MyGConnection(Base):
    __tablename__ = "myg_connections"
    user_low_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    user_high_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_low_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user_high_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    declined_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("user_low_id", "user_high_id", name="uq_conversation_pair"),)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    shared_post_id: Mapped[str | None] = mapped_column(ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(40), index=True)
    post_id: Mapped[str | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    comment_id: Mapped[str | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    myg_request_id: Mapped[str | None] = mapped_column(ForeignKey("myg_requests.id", ondelete="CASCADE"), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Update(Base):
    __tablename__ = "updates"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VerificationCode(Base):
    __tablename__ = "verification_codes"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(30), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Block(Base):
    __tablename__ = "blocks"
    blocker_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blocked_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SupportReport(Base):
    __tablename__ = "support_reports"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    app_area: Mapped[str] = mapped_column(String(120))
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class SupportAttachment(Base):
    __tablename__ = "support_attachments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("support_reports.id", ondelete="CASCADE"), index=True)
    storage_url: Mapped[str] = mapped_column(String(1000))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)


Index("ix_messages_conversation_created", Message.conversation_id, Message.created_at)
Index("ix_notifications_recipient_created", Notification.recipient_id, Notification.created_at)
