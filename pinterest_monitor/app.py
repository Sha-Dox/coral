from flask import Flask, render_template, request, jsonify
from database import (
    init_db, add_board, get_all_boards, get_board, 
    get_board_history, delete_board, update_pin_count, board_exists,
    add_user, get_all_users, get_user_by_username, delete_user, get_user_board_count
)
from monitor import PinterestMonitor
from scheduler import MonitorScheduler
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
monitor = PinterestMonitor()
scheduler = MonitorScheduler()

# Initialize database
init_db()

# Start scheduler
scheduler.start()

@app.route('/')
def index():
    """Serve the main web UI"""
    return render_template('index.html')

@app.route('/api/boards', methods=['GET'])
def api_get_boards():
    """Get all monitored boards"""
    boards = get_all_boards()
    return jsonify({'success': True, 'boards': boards})

@app.route('/api/board/<int:board_id>', methods=['GET'])
def api_get_board(board_id):
    """Get a specific board"""
    board = get_board(board_id)
    if board:
        return jsonify({'success': True, 'board': board})
    return jsonify({'success': False, 'error': 'Board not found'}), 404

@app.route('/api/board/<int:board_id>/history', methods=['GET'])
def api_get_board_history(board_id):
    """Get pin count history for a board"""
    limit = request.args.get('limit', 100, type=int)
    history = get_board_history(board_id, limit)
    return jsonify({'success': True, 'history': history})

@app.route('/api/board/<int:board_id>', methods=['DELETE'])
def api_delete_board(board_id):
    """Remove a board from monitoring"""
    success = delete_board(board_id)
    if success:
        return jsonify({'success': True, 'message': 'Board deleted'})
    return jsonify({'success': False, 'error': 'Board not found'}), 404

@app.route('/api/add-board', methods=['POST'])
def api_add_board():
    """Add a single board to monitoring"""
    data = request.json
    board_url = data.get('url', '').strip()
    
    if not board_url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    # Normalize URL
    board_url = monitor.normalize_url(board_url)
    
    # Check if already exists
    if board_exists(board_url):
        return jsonify({'success': False, 'error': 'Board already being monitored'}), 400
    
    # Get board info
    logger.info(f"Fetching board info for: {board_url}")
    board_info = monitor.get_board_info(board_url)
    
    if not board_info:
        return jsonify({'success': False, 'error': 'Could not fetch board information'}), 400
    
    # Add to database
    board_id = add_board(
        url=board_info['url'],
        name=board_info['name'],
        username=board_info['username'],
        pin_count=board_info['pin_count']
    )
    
    if board_id:
        logger.info(f"Added board: {board_info['name']} ({board_info['pin_count']} pins)")
        return jsonify({
            'success': True,
            'message': f"Added board: {board_info['name']}",
            'board_id': board_id
        })
    
    return jsonify({'success': False, 'error': 'Failed to add board'}), 500

@app.route('/api/add-user', methods=['POST'])
def api_add_user():
    """Add all boards for a Pinterest user"""
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'error': 'Username is required'}), 400
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Get user profile info
    logger.info(f"Fetching profile for user: {username}")
    user_info = monitor.get_user_info(username)
    
    if user_info:
        # Add or update user profile
        user_id = add_user(
            username=user_info['username'],
            display_name=user_info['display_name']
        )
        logger.info(f"Added/updated user profile: {user_info['display_name']}")
    
    logger.info(f"Fetching boards for user: {username}")
    boards = monitor.get_user_boards(username)
    
    if not boards:
        return jsonify({'success': False, 'error': f'Could not find boards for user: {username}'}), 400
    
    # Add each board
    added = []
    skipped = []
    
    for board_info in boards:
        if board_exists(board_info['url']):
            skipped.append(board_info['name'])
            continue
        
        board_id = add_board(
            url=board_info['url'],
            name=board_info['name'],
            username=board_info['username'],
            pin_count=board_info['pin_count']
        )
        
        if board_id:
            added.append(board_info['name'])
            logger.info(f"  Added: {board_info['name']} ({board_info['pin_count']} pins)")
    
    message = f"Added {len(added)} board(s) for user {username}"
    if skipped:
        message += f". Skipped {len(skipped)} already monitored."
    
    return jsonify({
        'success': True,
        'message': message,
        'added': added,
        'skipped': skipped
    })

@app.route('/api/check-now', methods=['POST'])
def api_check_now():
    """Manually trigger a check of all boards"""
    try:
        scheduler.run_now()
        return jsonify({'success': True, 'message': 'Check completed'})
    except Exception as e:
        logger.error(f"Error during manual check: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/board/<int:board_id>/check', methods=['POST'])
def api_check_single_board(board_id):
    """Manually trigger a check for a specific board"""
    try:
        success = scheduler.check_single_board(board_id)
        if success:
            return jsonify({'success': True, 'message': 'Board checked'})
        return jsonify({'success': False, 'error': 'Failed to check board'}), 500
    except Exception as e:
        logger.error(f"Error checking board {board_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# User/Profile endpoints

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all monitored user profiles with board counts"""
    users = get_all_users()
    # Add board count for each user
    for user in users:
        user['board_count'] = get_user_board_count(user['username'])
    return jsonify({'success': True, 'users': users})

@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """Remove a user profile and all their boards from monitoring"""
    success = delete_user(user_id)
    if success:
        return jsonify({'success': True, 'message': 'User and their boards deleted'})
    return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get overall statistics"""
    boards = get_all_boards()
    users = get_all_users()
    
    total_boards = len(boards)
    total_pins = sum(b['current_pin_count'] for b in boards)
    total_users = len(users)
    
    return jsonify({
        'success': True,
        'stats': {
            'total_boards': total_boards,
            'total_pins': total_pins,
            'total_users': total_users
        }
    })

@app.route('/api/check-now', methods=['POST'])
def api_check_now():
    """Manually trigger a check of all boards"""
    try:
        scheduler.run_now()
        return jsonify({'success': True, 'message': 'Check completed'})
    except Exception as e:
        logger.error(f"Error during manual check: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def api_config():
    """Get current configuration (non-sensitive values)"""
    return jsonify({
        'success': True,
        'config': {
            'check_interval': config.get_int('monitoring', 'check_interval'),
            'port': config.get_int('server', 'port')
        }
    })

def main():
    """Main entry point for the application"""
    try:
        host = config.get('server', 'host')
        port = config.get_int('server', 'port')
        debug = config.get_bool('server', 'debug')
        check_interval = config.get_int('monitoring', 'check_interval')
        
        print("\n" + "="*60)
        print("  Pinterest Monitor Started")
        print("="*60)
        print(f"  Web UI: http://localhost:{port}")
        print(f"  Checking boards every {check_interval} minutes")
        print("="*60 + "\n")
        
        app.run(debug=debug, host=host, port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()

if __name__ == '__main__':
    main()
