from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    telegram_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(String, default="Medium")  # High, Medium, Low
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, completed
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    remind_message = Column(String, nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="reminders")
    task = relationship("Task", back_populates="reminders")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def add_task(user_id: int, title: str, description: str = None, priority: str = "Medium", due_date: datetime = None):
    db = SessionLocal()
    get_or_create_user(user_id)
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Automatically schedule a reminder if due_date is set in the future
    if due_date and due_date > datetime.now():
        reminder = Reminder(
            user_id=user_id,
            task_id=task.id,
            remind_message=f"⏰ Reminder: {task.title}",
            remind_at=due_date
        )
        db.add(reminder)
        db.commit()
        
    return task

def get_open_tasks(user_id: int):
    db = SessionLocal()
    return db.query(Task).filter(Task.user_id == user_id, Task.status == "pending").order_by(Task.due_date.asc().nullslast()).all()

def mark_completed(user_id: int, task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task:
        task.status = "completed"
        task.completed_at = datetime.now()
        db.commit()
        return task
    return None

def delete_task(user_id: int, task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task:
        db.delete(task)
        db.commit()
        return True
    return False

def get_task_stats(user_id: int):
    db = SessionLocal()
    total = db.query(Task).filter(Task.user_id == user_id).count()
    completed = db.query(Task).filter(Task.user_id == user_id, Task.status == "completed").count()
    pending = db.query(Task).filter(Task.user_id == user_id, Task.status == "pending").count()
    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }

def get_due_reminders():
    db = SessionLocal()
    now = datetime.now()
    return db.query(Reminder).filter(Reminder.remind_at <= now, Reminder.is_sent == False).all()

def mark_reminder_sent(reminder_id: int):
    db = SessionLocal()
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder:
        reminder.is_sent = True
        db.commit()
