# 🤖 AI Agent Integration Guide

## How to Prompt Your AI Agent to Integrate with CORAL

This guide helps you instruct AI assistants (like Claude, ChatGPT, etc.) to integrate your OSINT monitoring tool with CORAL.

---

## 📋 Quick Prompt Template

Copy and paste this prompt to your AI assistant:

```
I have an OSINT monitoring tool that I want to integrate with CORAL 
(OSINT Repository Orchestration Project UI).

CORAL is a central dashboard at http://localhost:5002 that collects 
events from multiple monitoring tools via webhooks.

My tool monitors [PLATFORM_NAME] and detects [WHAT_IT_MONITORS].

Please help me:
1. Add webhook integration to send events to CORAL
2. Use the coral_notifier module for easy integration
3. Add auto-detection so my tool works standalone if CORAL isn't running
4. Make it send events for: [EVENT_TYPES]

The webhook endpoint is: http://localhost:5002/api/webhook/[platform_name]

Example event: {username: "johndoe", event_type: "new_post", summary: "New post detected"}
```

---

## 🎯 Detailed Integration Prompts

### For a New Monitor Tool

```
I'm building a [PLATFORM] monitoring tool and want to integrate it with CORAL.

Context:
- CORAL is running at http://localhost:5002
- It receives webhooks at /api/webhook/[platform_name]
- I want my tool to work both with and without CORAL

Requirements:
1. Use the coral_notifier.py helper module from /path/to/coral/coral/
2. Add auto-detection to check if CORAL is available
3. If CORAL is available, send webhooks
4. If CORAL is not available, run in standalone mode
5. Send events for: [list your event types]

My tool's main file is: [filename]
Current monitoring logic is in: [function/class name]

Please add the integration code with minimal changes to existing functionality.
```

### For Existing Monitor Modification

```
I have an existing [PLATFORM] monitor that I want to connect to CORAL.

Current setup:
- Monitor script: [path/to/script.py]
- It detects: [what it monitors]
- Current output: [how it outputs data]

CORAL integration needed:
- CORAL URL: http://localhost:5002
- Webhook endpoint: /api/webhook/[platform]
- Use coral_notifier.py helper module
- Auto-detect if CORAL is running
- Keep existing functionality if CORAL is down

Event types to send:
- [event_type_1]: When [condition]
- [event_type_2]: When [condition]

Please modify my code to integrate with CORAL while preserving standalone functionality.
```

---

## 📦 Integration Steps for AI

When prompting your AI, ask it to follow these steps:

### Step 1: Copy Helper Module
```
Copy the coral_notifier.py file from /path/to/coral/coral/ to my project.
OR: Import it directly if my tool is in the same repository.
```

### Step 2: Initialize Notifier
```python
from coral_notifier import CORALNotifier

# Auto-detects CORAL availability
notifier = CoralNotifier('my_platform_name')

# Check mode
if notifier.is_coral_mode():
    print("Connected to CORAL")
else:
    print("Running standalone")
```

### Step 3: Send Events
```python
# Send event when something is detected
notifier.send_event(
    username='detected_username',
    event_type='new_activity',
    summary='Brief description of what happened',
    data={'additional': 'context'}
)
```

---

## 🔧 Example Prompts by Use Case

### Use Case 1: Twitter/X Monitor

```
I'm building a Twitter/X monitor that tracks user tweets and profile changes.

Integration with CORAL:
- Platform name: twitter
- Webhook: http://localhost:5002/api/webhook/twitter
- Events to send:
  - new_tweet: When user posts a tweet
  - profile_update: When profile bio/picture changes
  - follower_change: When follower count changes significantly

Please:
1. Add coral_notifier.py integration
2. Auto-detect CORAL availability
3. Send events with username, event_type, summary, and tweet data
4. Keep standalone functionality if CORAL is unavailable

My current monitoring logic is in check_user_activity() function.
```

### Use Case 2: TikTok Monitor

```
I have a TikTok scraper that monitors for new videos.

Current behavior:
- Checks users every 5 minutes
- Prints new videos to console
- Stores data in local JSON file

CORAL Integration needed:
- Send webhook when new video detected
- Include: username, video_url, caption, view_count
- Platform name: tiktok
- Event type: new_video
- Use auto-detection

Please modify my scraper to send data to CORAL while keeping local storage.
```

### Use Case 3: LinkedIn Monitor

```
I'm monitoring LinkedIn profiles for job changes and posts.

Tool details:
- Language: Python
- Checks profiles from config file
- Currently sends email notifications

Want to add:
- CORAL webhook integration
- Events: job_change, new_post, profile_update
- Platform: linkedin
- Keep email notifications as fallback

Please integrate coral_notifier with auto-detection.
```

---

## 📝 Configuration Prompt

After integration, tell your AI:

```
Now help me add my new monitor to CORAL's config.yaml:

Add this section:
[platform_name]:
  enabled: true
  standalone: false
  port: [your_port]
  webhook:
    enabled: true
    url: "http://localhost:5002/api/webhook/[platform_name]"

Also update the database with trigger URL if needed.
```

---

## 🧪 Testing Prompts

```
Help me test the CORAL integration:

1. Test with CORAL running:
   - Start CORAL: cd coral && python3 app.py
   - Start my monitor: python3 my_monitor.py
   - Verify events appear at http://localhost:5002

2. Test standalone mode:
   - Stop CORAL
   - Start my monitor
   - Verify it runs normally without errors

3. Test auto-detection:
   - Run demo: python3 demo_auto_detection.py
   - Should show my platform in INTEGRATED or STANDALONE mode
```

---

## 📖 Documentation Prompts

```
Create documentation for my CORAL-integrated monitor:

Include:
- How to run standalone
- How to run with CORAL
- Configuration options
- Event types sent
- Example webhook payloads

Format as README.md
```

---

## 🎨 Example Complete Prompt

Here's a complete prompt you can customize:

```
I'm building a [PLATFORM] monitor that [WHAT IT DOES].

CORAL Integration:

CORAL Setup:
- URL: http://localhost:5002
- Webhook endpoint: /api/webhook/[platform]
- Helper module: coral/coral/coral_notifier.py

My Monitor:
- Platform: [platform_name]
- Port: [port_number]
- Current script: [path/to/script.py]
- Monitoring logic: [function/class name]

Events to Send:
1. [event_type_1]: When [trigger_condition]
   - Username: [where to get it]
   - Data: [what additional info to include]

2. [event_type_2]: When [trigger_condition]
   - Username: [where to get it]
   - Data: [what additional info to include]

Requirements:
1. Import and use coral_notifier.py
2. Auto-detect if CORAL is available (<500ms check)
3. If available: send webhooks
4. If not available: run standalone (current behavior)
5. Log the operating mode on startup
6. Minimal changes to existing code

Please:
- Add the integration code
- Update my monitoring logic to send events
- Add configuration to config.yaml
- Create a simple test script

Preserve:
- All existing functionality
- Standalone operation
- Current data storage/output
```

---

## 💡 Tips for Better AI Integration

### Be Specific About Your Tool

```
Good: "I have a Python script that uses Selenium to check Instagram profiles every 10 minutes"
Bad: "I have a monitor"
```

### Provide File Paths

```
Good: "My script is at ./monitors/instagram_check.py and uses check_user() function"
Bad: "It's in a file somewhere"
```

### Describe Current Behavior

```
Good: "Currently prints to console and saves to data.json, want to add CORAL webhooks while keeping both"
Bad: "Want to add CORAL"
```

### Specify Event Structure

```
Good: "Send event with username from profile.username, event_type='new_post', and include post_url in data"
Bad: "Send events"
```

---

## 🔗 Reference Materials to Share with AI

Provide these to your AI assistant:

1. **CORAL Notifier Code**:
   ```
   Show AI: /path/to/coral/coral/coral_notifier.py
   ```

2. **Example Integration**:
   ```
   Reference: Instagram monitor at /path/to/coral/instagram_monitor/
   ```

3. **Webhook Format**:
   ```json
   {
     "username": "user123",
     "event_type": "new_post",
     "summary": "Posted a new photo",
     "event_time": "2026-02-07T23:00:00Z",
     "data": {
       "post_id": "123456",
       "url": "https://...",
       "custom_field": "value"
     }
   }
   ```

4. **Config Format**:
   ```yaml
   my_platform:
     enabled: true
     port: 8002
     webhook:
       enabled: true
       url: "http://localhost:5002/api/webhook/my_platform"
   ```

---

## ✅ Verification Prompt

After integration, ask your AI:

```
Verify the CORAL integration:

Checklist:
- [ ] coral_notifier imported correctly
- [ ] Auto-detection on startup
- [ ] Events sent with username, event_type, summary
- [ ] Works standalone if CORAL not running
- [ ] No errors in either mode
- [ ] Logs show "INTEGRATED" or "STANDALONE" mode

Test commands:
1. With CORAL: [command]
2. Without CORAL: [command]
3. Check events: curl http://localhost:5002/api/events/[platform]
```

---

## 📚 Additional Resources

- **CORAL Documentation**: See README.md
- **Integration Examples**: See existing monitors (instagram_monitor/, pinterest_monitor/, spotify_monitor/)
- **Webhook API**: See coral/README.md API section
- **Helper Module**: See coral/coral_notifier.py

---

## 🆘 Troubleshooting Prompts

If integration isn't working:

```
My CORAL integration isn't working:

Issue: [describe the problem]
Error message: [paste error]

Current setup:
- Platform: [name]
- CORAL running: [yes/no]
- Events being sent: [yes/no]
- Logs show: [paste relevant logs]

Please help debug:
1. Check if coral_notifier is imported correctly
2. Verify webhook URL format
3. Test CORAL availability check
4. Review event payload format
```

---

**Pro Tip**: Start with a simple integration (one event type) and expand from there. This makes debugging easier!

---

**CORAL**: Making OSINT monitoring collaborative and centralized.
