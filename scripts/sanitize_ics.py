import re

def sanitize_ics(input_file, output_file):
    # Tags we want to remove
    tags_to_remove = [
        'ATTENDEE', 
        'DESCRIPTION', 
        'ORGANIZER', 
        'X-ALT-DESC',  # Often contains HTML descriptions
        'X-MS-OLK-WIDGETINFO' # Outlook specific metadata
    ]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sanitized_lines = []
    skip_mode = False

    for line in lines:
        # Check if the line starts with any of our target tags
        # We use startswith because tags can have parameters (e.g., ATTENDEE;CN=John...)
        if any(line.startswith(tag) for tag in tags_to_remove):
            # iCalendar lines can be "folded" (continued on the next line with a space)
            # We need to skip the current line and any subsequent folded lines
            skip_mode = True
            continue
        
        # If the line starts with a space or tab, it's a continuation of the previous line
        if skip_mode and (line.startswith(' ') or line.startswith('\t')):
            continue
        
        # If we hit a new tag, stop skipping
        skip_mode = False
        sanitized_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(sanitized_lines)

    print(f"Sanitization complete! Saved to: {output_file}")

# Usage
sanitize_ics('my_calendar.ics', 'sanitized_calendar.ics')