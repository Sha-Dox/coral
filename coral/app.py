#!/usr/bin/env python3
"""
CORAL - Unified monitoring dashboard
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from dateutil import parser as date_parser
import json
import logging

import config
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize database
db.init_db()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

# Webhook API
@app.route('/api/webhook/<platform_name>', methods=['POST'])
def webhook_receiver(platform_name):
    """Receive webhook from monitors"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'}), 400
        
        # Validate required fields
        required = ['username', 'event_type', 'summary']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400
        
        # Look up platform
        platform = db.get_platform_by_name(platform_name)
        if not platform:
            return jsonify({
                'success': False,
                'error': f'Unknown platform: {platform_name}'
            }), 404
        
        # Validate webhook secret if configured
        if platform['webhook_secret']:
            auth_header = request.headers.get('X-Webhook-Secret', '')
            if auth_header != platform['webhook_secret']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid webhook secret'
                }), 403
        
        # Parse event_time
        event_time = None
        if 'event_time' in data and data['event_time']:
            try:
                event_time = date_parser.parse(data['event_time'])
            except Exception as e:
                logger.warning(f"Could not parse event_time: {e}")
        
        # Store event
        event_id = db.add_event(
            platform_id=platform['id'],
            platform_username=data['username'],
            event_type=data['event_type'],
            summary=data['summary'],
            event_time=event_time,
            event_data=data.get('data')
        )
        
        logger.info(f"Received {platform_name} event: {data['event_type']} from @{data['username']}")
        
        return jsonify({
            'success': True,
            'event_id': event_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Persons API
@app.route('/api/persons', methods=['GET'])
def api_get_persons():
    """Get all persons with their latest activity"""
    try:
        persons = db.get_all_persons()
        
        # Enrich with latest event info
        for person in persons:
            latest = db.get_person_latest_event(person['id'])
            person['latest_event'] = latest
        
        return jsonify({'success': True, 'persons': persons})
    except Exception as e:
        logger.error(f"Error getting persons: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['GET'])
def api_get_person(person_id):
    """Get a specific person"""
    try:
        person = db.get_person(person_id)
        if not person:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        # Add latest event
        latest = db.get_person_latest_event(person_id)
        person['latest_event'] = latest
        
        return jsonify({'success': True, 'person': person})
    except Exception as e:
        logger.error(f"Error getting person: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persons', methods=['POST'])
def api_create_person():
    """Create a new person"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        person_id = db.add_person(name, data.get('notes'))
        
        return jsonify({
            'success': True,
            'person_id': person_id,
            'message': f'Created person: {name}'
        }), 201
    except Exception as e:
        logger.error(f"Error creating person: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['PUT'])
def api_update_person(person_id):
    """Update a person"""
    try:
        data = request.get_json()
        success = db.update_person(
            person_id,
            name=data.get('name'),
            notes=data.get('notes')
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        return jsonify({'success': True, 'message': 'Person updated'})
    except Exception as e:
        logger.error(f"Error updating person: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/persons/<int:person_id>', methods=['DELETE'])
def api_delete_person(person_id):
    """Delete a person"""
    try:
        success = db.delete_person(person_id)
        if not success:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        return jsonify({'success': True, 'message': 'Person deleted'})
    except Exception as e:
        logger.error(f"Error deleting person: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Linked profiles API
@app.route('/api/persons/<int:person_id>/profiles', methods=['POST'])
def api_link_profile(person_id):
    """Link a platform profile to a person"""
    try:
        data = request.get_json()
        platform_id = data.get('platform_id')
        username = data.get('username', '').strip()
        
        if not platform_id or not username:
            return jsonify({
                'success': False,
                'error': 'platform_id and username are required'
            }), 400
        
        profile_id = db.link_profile(person_id, platform_id, username)
        if not profile_id:
            return jsonify({
                'success': False,
                'error': 'Username already linked (possibly to another person)'
            }), 400
        
        return jsonify({
            'success': True,
            'profile_id': profile_id,
            'message': 'Profile linked'
        }), 201
    except Exception as e:
        logger.error(f"Error linking profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
def api_unlink_profile(profile_id):
    """Unlink a profile"""
    try:
        success = db.unlink_profile(profile_id)
        if not success:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
        
        return jsonify({'success': True, 'message': 'Profile unlinked'})
    except Exception as e:
        logger.error(f"Error unlinking profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Events API
@app.route('/api/events', methods=['GET'])
def api_get_events():
    """Get events with optional filters"""
    try:
        platform_id = request.args.get('platform_id', type=int)
        person_id = request.args.get('person_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        events = db.get_events(
            platform_id=platform_id,
            person_id=person_id,
            limit=min(limit, 500),
            offset=offset
        )
        
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/unlinked', methods=['GET'])
def api_get_unlinked_events():
    """Get events not linked to any person"""
    try:
        limit = request.args.get('limit', 50, type=int)
        events = db.get_unlinked_events(limit=min(limit, 200))
        
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"Error getting unlinked events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Platforms API
@app.route('/api/platforms', methods=['GET'])
def api_get_platforms():
    """Get all platforms"""
    try:
        platforms = db.get_all_platforms()
        
        # Add webhook URL for each platform
        for platform in platforms:
            platform['webhook_url'] = f"{request.url_root}api/webhook/{platform['name']}"
        
        return jsonify({'success': True, 'platforms': platforms})
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/platforms/<int:platform_id>', methods=['PUT'])
def api_update_platform(platform_id):
    """Update platform settings"""
    try:
        data = request.get_json()
        success = db.update_platform(
            platform_id,
            display_name=data.get('display_name'),
            webhook_secret=data.get('webhook_secret'),
            trigger_url=data.get('trigger_url'),
            config_json=data.get('config_json')
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Platform not found'}), 404
        
        return jsonify({'success': True, 'message': 'Platform updated'})
    except Exception as e:
        logger.error(f"Error updating platform: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/platforms/<int:platform_id>/trigger', methods=['POST'])
def api_trigger_platform_check(platform_id):
    """Trigger a manual check for a platform"""
    try:
        import requests as req
        
        platform = db.get_platform_by_name(None)
        # Get platform by ID
        platforms = db.get_all_platforms()
        platform = next((p for p in platforms if p['id'] == platform_id), None)
        
        if not platform:
            return jsonify({'success': False, 'error': 'Platform not found'}), 404
        
        if not platform.get('trigger_url'):
            return jsonify({
                'success': False,
                'error': 'No trigger URL configured for this platform'
            }), 400
        
        # Send POST request to monitor's trigger endpoint
        try:
            response = req.post(
                platform['trigger_url'],
                timeout=10,
                json={'source': 'osint_hub'}
            )
            
            if response.status_code == 200:
                logger.info(f"Triggered check for {platform['name']}")
                return jsonify({
                    'success': True,
                    'message': f"Check triggered for {platform['display_name']}"
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Monitor returned status {response.status_code}"
                }), 500
        except req.exceptions.RequestException as e:
            logger.error(f"Failed to trigger {platform['name']}: {e}")
            return jsonify({
                'success': False,
                'error': f"Could not connect to monitor: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error triggering platform check: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Config/Stats API
@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get overall statistics"""
    try:
        persons = db.get_all_persons()
        platforms = db.get_all_platforms()
        
        # Count total profiles
        total_profiles = sum(len(p['profiles']) for p in persons)
        
        # Count recent events (last 24h)
        recent_events = db.get_events(limit=1000)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        recent_count = 0
        
        for e in recent_events:
            if e.get('event_time'):
                try:
                    event_dt = date_parser.parse(e['event_time'])
                    # Make timezone-aware if needed
                    if event_dt.tzinfo is None:
                        event_dt = event_dt.replace(tzinfo=timezone.utc)
                    if (now - event_dt).total_seconds() < 86400:
                        recent_count += 1
                except:
                    pass
        
        return jsonify({
            'success': True,
            'stats': {
                'total_persons': len(persons),
                'total_platforms': len(platforms),
                'total_profiles': total_profiles,
                'recent_events': recent_count
            }
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        db.get_all_platforms()
        
        return jsonify({
            'status': 'healthy',
            'service': 'CORAL Hub',
            'version': '1.0',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  CORAL Started")
    print("="*60)
    print(f"  Web UI: http://localhost:{config.PORT}")
    print(f"  Webhook endpoint: http://localhost:{config.PORT}/api/webhook/<platform>")
    print(f"  Health check: http://localhost:{config.PORT}/api/health")
    print("="*60 + "\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        use_reloader=False
    )
