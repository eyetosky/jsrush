"""
WebSocket Support for Real-time Features
Handles real-time game updates, notifications, and live stats
"""
from flask import Flask, request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask_socketio import rooms
import json
import logging
from datetime import datetime
from functools import wraps

# Initialize SocketIO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='gevent',
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

# Connection tracking
connected_users = {}  # user_id -> {sid, rooms, connected_at}
user_rooms = {}  # user_id -> set of room names


def init_socketio(app: Flask):
    """Initialize SocketIO with Flask app"""
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('FRONTEND_URL', '*'),
        async_mode='gevent',
        ping_timeout=60,
        ping_interval=25
    )
    
    # Register event handlers
    register_handlers()
    
    # Background tasks
    start_background_tasks(app)
    
    return socketio


def register_handlers():
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection"""
        if not current_user.is_authenticated:
            return False  # Reject unauthenticated connections
        
        sid = request.sid
        user_id = current_user.id
        
        # Track connection
        connected_users[user_id] = {
            'sid': sid,
            'rooms': set(),
            'connected_at': datetime.utcnow().isoformat()
        }
        user_rooms[user_id] = set()
        
        # Join user-specific room
        join_room(f"user_{current_user.id}")
        user_rooms[user_id].add(f"user_{current_user.id}")
        
        # Join global room for broadcasts
        join_room('global')
        user_rooms[user_id].add('global')
        
        # Emit connection confirmation
        emit('connected', {
            'message': "Connected to J\'sRush",
            'user_id': current_user.id,
            'balance': current_user.balance,
            'server_time': datetime.utcnow().isoformat()
        })
        
        # Notify others in global room
        emit('user_joined', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room='global', include_self=False)
        
        logging.info(f"User {current_user.id} connected via WebSocket")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if not current_user.is_authenticated:
            return
        
        user_id = current_user.id
        
        # Leave all rooms
        for room in user_rooms.get(user_id, set()):
            leave_room(room)
        
        # Notify others
        emit('user_left', {
            'user_id': user_id
        }, room='global')
        
        # Cleanup
        connected_users.pop(user_id, None)
        user_rooms.pop(user_id, None)
        
        logging.info(f"User {user_id} disconnected from WebSocket")
    
    @socketio.on('join_game')
    def handle_join_game(data):
        """Join a game-specific room"""
        if not current_user.is_authenticated:
            return
        
        game_type = data.get('game_type')
        game_id = data.get('game_id')
        
        if not game_type:
            emit('error', {'message': 'Game type required'})
            return
        
        room = f"game_{game_type}_{game_id}" if game_id else f"game_{game_type}"
        join_room(room)
        
        user_rooms[current_user.id].add(room)
        
        emit('joined_game', {
            'game_type': game_type,
            'game_id': game_id,
            'room': room
        })
        
        # Notify others in room
        emit('player_joined', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=room, include_self=False)
    
    @socketio.on('leave_game')
    def handle_leave_game(data):
        """Leave a game room"""
        if not current_user.is_authenticated:
            return
        
        game_type = data.get('game_type')
        game_id = data.get('game_id')
        
        room = f"game_{game_type}_{game_id}" if game_id else f"game_{game_type}"
        leave_room(room)
        
        if current_user.id in user_rooms:
            user_rooms[current_user.id].discard(room)
        
        emit('left_game', {
            'game_type': game_type,
            'game_id': game_id
        })
        
        # Notify others
        emit('player_left', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=room, include_self=False)
    
    @socketio.on('game_action')
    def handle_game_action(data):
        """Handle real-time game actions"""
        if not current_user.is_authenticated:
            return
        
        game_type = data.get('game_type')
        action = data.get('action')
        payload = data.get('payload', {})
        
        # Validate and broadcast to game room
        room = f"game_{game_type}_{payload.get('game_id', 'global')}"
        
        # Broadcast to other players in the game
        emit('game_action', {
            'user_id': current_user.id,
            'username': current_user.username,
            'action': action,
            'payload': payload,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room, include_self=False)
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Handle chat messages in game rooms"""
        if not current_user.is_authenticated:
            return
        
        room = data.get('room')
        message = data.get('message', '').strip()
        
        if not message or len(message) > 500:
            return
        
        # Broadcast to room
        emit('chat_message', {
            'user_id': current_user.id,
            'username': current_user.username,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room)
    
    @socketio.on('request_balance')
    def handle_balance_request():
        """Send current balance to client"""
        if not current_user.is_authenticated:
            return
        
        from models import db, User
        user = db.session.get(User, current_user.id)
        if user:
            emit('balance_update', {
                'balance': round(user.balance, 2),
                'currency': 'NGN'
            })
    
    @socketio.on('subscribe_notifications')
    def handle_subscribe_notifications():
        """Subscribe to notification channel"""
        if not current_user.is_authenticated:
            return
        
        join_room(f'notifications_{current_user.id}')
        emit('notification_subscribed', {'status': 'subscribed'})
    
    @socketio.on('unsubscribe_notifications')
    def handle_unsubscribe_notifications():
        """Unsubscribe from notification channel"""
        if not current_user.is_authenticated:
            return
        
        leave_room(f'notifications_{current_user.id}')
        emit('notification_unsubscribed', {'status': 'unsubscribed'})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for keepalive"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})


# Helper functions for emitting events

def emit_balance_update(user_id: int, balance: float):
    """Emit balance update to user"""
    socketio.emit('balance_update', {
        'balance': round(balance, 2),
        'currency': 'NGN'
    }, room=f'user_{user_id}')


def emit_notification(user_id: int, notification: dict):
    """Emit notification to user"""
    socketio.emit('notification', notification, room=f'notifications_{user_id}')


def emit_game_event(game_type: str, game_id: str, event: str, data: dict):
    """Emit game event to game room"""
    room = f"game_{game_type}_{game_id}"
    socketio.emit('game_event', {
        'event': event,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f"game_{game_type}_{game_id}")


def emit_global_announcement(message: str, level: str = 'info'):
    """Emit global announcement to all connected users"""
    socketio.emit('announcement', {
        'message': message,
        'level': level,
        'timestamp': datetime.utcnow().isoformat()
    }, room='global')


def emit_game_result(user_id: int, game_type: str, result: dict):
    """Emit game result to user"""
    socketio.emit('game_result', {
        'game_type': game_type,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'user_{user_id}')


def emit_transaction_update(user_id: int, transaction: dict):
    """Emit transaction update to user"""
    socketio.emit('transaction_update', transaction, room=f'user_{user_id}')


def emit_leaderboard_update(leaderboard: list):
    """Emit leaderboard update to global room"""
    socketio.emit('leaderboard_update', {
        'leaderboard': leaderboard,
        'timestamp': datetime.utcnow().isoformat()
    }, room='global')


def emit_jackpot_update(game_type: str, amount: float, winner_id: int = None):
    """Emit jackpot update"""
    socketio.emit('jackpot_update', {
        'game_type': game_type,
        'amount': amount,
        'winner_id': winner_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room='global')


# Authentication decorator for SocketIO
def authenticated_only(f):
    """Decorator to ensure user is authenticated for SocketIO events"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
            return False
        return f(*args, **kwargs)
    return f


# Background tasks for real-time updates
def start_background_tasks(app):
    """Start background tasks for real-time updates"""
    from threading import Thread
    import time
    
    def broadcast_balances():
        """Periodically broadcast balance updates"""
        while True:
            time.sleep(30)  # Every 30 seconds
            # In production, this would fetch from DB and emit to connected users
    
    def broadcast_jackpots():
        """Broadcast jackpot updates"""
        while True:
            time.sleep(10)  # Every 10 seconds
            # Fetch current jackpots and broadcast
    
    def broadcast_online_count():
        """Broadcast online user count"""
        while True:
            time.sleep(60)  # Every minute
            count = len(connected_users)
            socketio.emit('online_count', {'count': count}, room='global')
    
    # Start background threads
    threads = [
        Thread(target=broadcast_balances, daemon=True),
        Thread(target=broadcast_jackpots, daemon=True),
        Thread(target=broadcast_online_count, daemon=True)
    ]
    
    for t in threads:
        t.start()


def init_websocket(app):
    """Initialize WebSocket for the app"""
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('FRONTEND_URL', '*'),
        async_mode='gevent',
        ping_timeout=60,
        ping_interval=25,
        logger=False,
        engineio_logger=False
    )
    
    register_handlers()
    start_background_tasks(app)
    
    return socketio


# Utility functions for sending notifications
def send_notification(user_id: int, notification: dict):
    """Send notification to specific user"""
    from flask_socketio import SocketIO
    from flask import current_app
    
    if hasattr(current_app, 'socketio'):
        current_app.socketio.emit('notification', notification, room=f'notifications_{user_id}')


def send_game_invite(user_id: int, game_type: str, game_id: str, inviter: str):
    """Send game invitation to user"""
    socketio.emit('game_invite', {
        'game_type': game_type,
        'game_id': game_id,
        'inviter': inviter,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'notifications_{user_id}')


def broadcast_system_message(message: str, level: str = 'info'):
    """Broadcast system message to all users"""
    socketio.emit('system_message', {
        'message': message,
        'level': level,
        'timestamp': datetime.utcnow().isoformat()
    }, room='global')


# Context manager for emitting from background tasks
class SocketIOContext:
    """Context manager for using SocketIO outside request context"""
    
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
    
    def __enter__(self):
        return self.socketio
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def get_socketio():
    """Get socketio instance for use in background tasks"""
    return socketio