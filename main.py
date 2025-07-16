#!/usr/bin/env python
import sqlite3
import os
import json

def read_messages(db, limit=100, by_group=True):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = """
        SELECT 
            chat.ROWID AS chat_id,
            message.ROWID AS message_id, 
            chat.account_login AS apple_id,
            message.service AS message_type,
            datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') AS message_date_str,
            message.date AS message_date,
            CASE message.is_from_me
                WHEN 1 THEN message.destination_caller_id
                ELSE chat.chat_identifier
            END AS sender,
            CASE message.is_from_me
                WHEN 0 THEN message.destination_caller_id
                ELSE chat.chat_identifier
            END AS receiver,
            message.attributedBody AS format_text
        FROM 
            message
        JOIN
            chat_message_join ON chat_message_join.message_id = message.ROWID
        JOIN
            chat on chat.ROWID = chat_message_join.chat_id
        JOIN 
            handle ON message.handle_id = handle.ROWID
    """
    
    if by_group:
        # append chat_id group order by
        query += """
        JOIN (
            SELECT
                chat.ROWID AS chat_id,
                MAX(message.date) AS max_date
            FROM
                chat
            JOIN
                chat_message_join ON chat.ROWID = chat_message_join.chat_id
            JOIN
                message ON message.ROWID = chat_message_join.message_id
            GROUP BY
                chat.ROWID
        ) max_dates ON chat.ROWID = max_dates.chat_id
        ORDER BY 
            max_dates.max_date DESC,
            message.date DESC
        """
    else:
        # order by message desc
        query += """
        ORDER BY
            message.date DESC
        """
    
    if limit is not None:
        query += f"LIMIT {limit}"

    results = cursor.execute(query).fetchall()
    messages = []

    for result in results:
        chat_id, message_id, apple_id, message_type, message_date_str, message_date, sender, receiver, format_text = result
        body = ""

        if format_text is None:
            continue

        format_text = format_text.decode('utf-8', errors='replace')
        if "NSNumber" in str(format_text):
            format_text = str(format_text).split("NSNumber")[0]
            if "NSString" in format_text:
                format_text = str(format_text).split("NSString")[1]
                if "NSDictionary" in format_text:
                    format_text = str(format_text).split("NSDictionary")[0]
                    format_text = format_text[8:-12]
                    body = format_text
        
        messages.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "apple_id": apple_id,
            "message_type": message_type,
            "message_date_str": message_date_str, 
            "message_date": message_date, 
            "sender": sender, 
            "receiver": receiver,
            "body": body
        })
    return messages

if __name__ == "__main__":
    messages = read_messages(os.path.expanduser("~/Library/Messages/chat.db"), 10)
    for message in messages:
        print(json.dumps(message, indent=4, ensure_ascii=False))
