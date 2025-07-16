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