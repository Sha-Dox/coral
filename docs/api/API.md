# API Documentation

## CORAL Hub API

Base URL: `http://localhost:5002`

### Health Check

**GET** `/api/health`

Check service health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "service": "CORAL Hub",
  "version": "1.0",
  "timestamp": "2026-02-08T00:00:00"
}
```

---

### Webhook API

**POST** `/api/webhook/<platform>`

Receive events from monitors.

**Parameters:**
- `platform` - Platform name (instagram, pinterest, spotify)

**Request Body:**
```json
{
  "username": "johndoe",
  "event_type": "new_post",
  "summary": "New post detected",
  "event_time": "2026-02-08T00:00:00Z",
  "data": {
    "post_id": "123",
    "caption": "Example"
  }
}
```

**Response:**
```json
{
  "success": true,
  "event_id": 42
}
```

---

### Persons API

**GET** `/api/persons`

Get all persons with linked profiles.

**Response:**
```json
{
  "success": true,
  "persons": [
    {
      "id": 1,
      "name": "John Doe",
      "notes": "",
      "profiles": [
        {
          "platform": "instagram",
          "username": "johndoe"
        }
      ]
    }
  ]
}
```

**POST** `/api/persons`

Create a new person.

**Request Body:**
```json
{
  "name": "John Doe",
  "notes": "Optional notes"
}
```

**PUT** `/api/persons/<id>`

Update a person.

**DELETE** `/api/persons/<id>`

Delete a person.

---

### Profiles API

**POST** `/api/persons/<person_id>/profiles`

Link a profile to a person.

**Request Body:**
```json
{
  "platform_id": 1,
  "platform_username": "johndoe"
}
```

**DELETE** `/api/persons/<person_id>/profiles/<profile_id>`

Unlink a profile from a person.

---

### Events API

**GET** `/api/events`

Get recent events.

**Query Parameters:**
- `limit` - Number of events (default: 100)
- `platform_id` - Filter by platform
- `person_id` - Filter by person

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": 1,
      "platform": "instagram",
      "username": "johndoe",
      "event_type": "new_post",
      "summary": "New post detected",
      "event_time": "2026-02-08T00:00:00Z",
      "person": "John Doe"
    }
  ]
}
```

---

### Platforms API

**GET** `/api/platforms`

Get all configured platforms.

**PUT** `/api/platforms/<id>`

Update platform configuration.

**POST** `/api/platforms/<id>/trigger`

Manually trigger a platform check.

---

### Statistics API

**GET** `/api/stats`

Get dashboard statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_persons": 10,
    "total_platforms": 3,
    "total_profiles": 25,
    "recent_events_24h": 42
  }
}
```

---

### Maigret Search API

**POST** `/api/maigret/search`

Search a username across public sites using Maigret.

**Request Body:**
```json
{
  "username": "johndoe",
  "top_sites": 500,
  "timeout": 5,
  "max_connections": 50,
  "retries": 0,
  "tags": "social, coding",
  "site_list": "GitHub, Reddit",
  "include_disabled": false,
  "check_domains": false,
  "use_cookies": false,
  "all_sites": false,
  "id_type": "username"
}
```

**Response:**
```json
{
  "success": true,
  "username": "johndoe",
  "stats": {
    "checked_sites": 500,
    "scope_sites": 500,
    "found_sites": 12,
    "duration_ms": 4200,
    "top_sites": 500
  },
  "filters": {
    "tags": ["social", "coding"],
    "site_list": ["GitHub", "Reddit"],
    "include_disabled": false,
    "check_domains": false,
    "use_cookies": false,
    "id_type": "username"
  },
  "found": [
    {
      "site_name": "GitHub",
      "url": "https://github.com/johndoe",
      "status": "Claimed",
      "tags": ["coding"]
    }
  ]
}
```

---

## Monitor Integration

### Sending Events to CORAL

Use the `CoralNotifier` class:

```python
from coral_notifier import CoralNotifier

notifier = CoralNotifier('instagram')

notifier.send_event(
    username='johndoe',
    event_type='new_post',
    summary='New post detected',
    data={'post_id': '123'}
)
```

### Event Types

Common event types:
- `new_post` - New content posted
- `bio_change` - Profile bio updated
- `follower_change` - Follower count changed
- `name_change` - Display name changed
- `avatar_change` - Profile picture changed
- `new_pin` - New Pinterest pin
- `song_change` - Spotify listening activity
- `playlist_update` - Playlist modified

---

## Rate Limiting

Default: 100 requests per minute per IP

Response when rate limited:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Error Responses

All errors return:
```json
{
  "success": false,
  "error": "Error message description"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `429` - Rate Limited
- `500` - Server Error
- `503` - Service Unhealthy
