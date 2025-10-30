import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


game_participants = db.Table('game_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('game_room_id', db.Integer, db.ForeignKey('game_room.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    segments = db.relationship('StorySegment', back_populates='author', lazy=True)
    game_rooms = db.relationship('GameRoom', secondary=game_participants, 
                                 back_populates='participants', lazy='dynamic')
    
    def __init__(self, username=None, email=None):
        self.username = username
        self.email = email

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.email})>'

class GameRoom(db.Model):
    __tablename__ = 'game_room'
    
    id = db.Column(db.Integer, primary_key=True)
    
    room_code = db.Column(db.String(8), unique=True, nullable=False)
    
    status = db.Column(db.String(20), default='LOBBY', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    final_story_text = db.Column(db.Text, nullable=True)

    participants = db.relationship('User', secondary=game_participants, 
                                   back_populates='game_rooms', lazy='dynamic')
    
    segments = db.relationship('StorySegment', back_populates='game_room', 
                               lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<GameRoom {self.room_code} ({self.status})>'

class StorySegment(db.Model):
    __tablename__ = 'story_segment'
    
    id = db.Column(db.Integer, primary_key=True)
    text_content = db.Column(db.Text, nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', back_populates='segments')

    game_room_id = db.Column(db.Integer, db.ForeignKey('game_room.id'), nullable=False)
    game_room = db.relationship('GameRoom', back_populates='segments')

    def __repr__(self):
        return f'<Segment (Round {self.round_number}) by {self.author.username}>'