from kafka import KafkaConsumer
import json
import mysql.connector
from mysql.connector import Error
import time
import logging
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="host.docker.internal",
            port=3306,
            database="attendance",
            user="root",
            password="1234"
        )
        logger.info("Successfully connected to MySQL database")
        return connection
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def handle_message(msg_value):
    if not msg_value:
        logger.warning("Received empty message")
        return None
    try:
        if isinstance(msg_value, bytes):
            msg_value = msg_value.decode('utf-8')
        return json.loads(msg_value) if isinstance(msg_value, str) else msg_value
    except Exception as e:
        logger.error(f"Error decoding message: {e}")
        return None

def handle_ceo_changes(cursor, operation, data):
    try:
        if operation == 'c':  # Insert
            sql = """INSERT INTO ceo (name, position) VALUES (%s, %s)"""
            values = (data['after']['name'], data['after']['position'])
        elif operation == 'u':  # Update
            sql = """UPDATE ceo SET position = %s WHERE name = %s"""
            values = (data['after']['position'], data['after']['name'])
        elif operation == 'd':  # Delete
            sql = """DELETE FROM ceo WHERE name = %s"""
            values = (data['before']['name'],)
        
        cursor.execute(sql, values)
        logger.info(f"CEO table - Executed {operation} operation: {values}")
        return True
    except Exception as e:
        logger.error(f"Error handling CEO change: {e}")
        return False

def handle_employee_changes(cursor, operation, data):
    try:
        if operation == 'c':  # Insert
            sql = """INSERT INTO employee (name, department, position) 
                    VALUES (%s, %s, %s)"""
            values = (data['after']['name'], data['after']['department'], 
                     data['after']['position'])
        elif operation == 'u':  # Update
            sql = """UPDATE employee 
                    SET department = %s, position = %s 
                    WHERE name = %s"""
            values = (data['after']['department'], data['after']['position'], 
                     data['after']['name'])
        elif operation == 'd':  # Delete
            sql = """DELETE FROM employee WHERE name = %s"""
            values = (data['before']['name'],)
        
        cursor.execute(sql, values)
        logger.info(f"Employee table - Executed {operation} operation: {values}")
        return True
    except Exception as e:
        logger.error(f"Error handling Employee change: {e}")
        return False

def process_messages(topic, handler_func):
    while True:
        try:
            connection = connect_to_database()
            if not connection:
                time.sleep(5)
                continue

            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=['kafka:29092'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=f'{topic}_sync_group',
                value_deserializer=None
            )
            
            logger.info(f"Started consuming messages from topic: {topic}")
            
            for message in consumer:
                try:
                    decoded_message = handle_message(message.value)
                    if not decoded_message or 'payload' not in decoded_message:
                        continue

                    cursor = connection.cursor()
                    data = decoded_message['payload']
                    operation = data['op']
                    
                    if handler_func(cursor, operation, data):
                        connection.commit()
                    else:
                        connection.rollback()
                    
                    cursor.close()
                except Exception as e:
                    logger.error(f"Error processing message from {topic}: {e}")
                    if 'cursor' in locals():
                        cursor.close()
                    connection.rollback()

        except Exception as e:
            logger.error(f"Error in {topic} consumer: {e}")
            if 'connection' in locals() and connection:
                connection.close()
            time.sleep(5)

def main():
    logger.info("Starting sync service...")

    # 정확한 토픽 이름 지정
    ceo_topic = 'mysql-ceo.member.ceo'
    employee_topic = 'mysql-employee.member.employee'

    logger.info(f"Subscribing to topics: {ceo_topic} and {employee_topic}")

    # CEO 변경사항 처리를 위한 스레드
    ceo_thread = threading.Thread(
        target=process_messages,
        args=(ceo_topic, handle_ceo_changes)
    )
    
    # Employee 변경사항 처리를 위한 스레드
    employee_thread = threading.Thread(
        target=process_messages,
        args=(employee_topic, handle_employee_changes)
    )
    
    ceo_thread.start()
    employee_thread.start()
    
    try:
        ceo_thread.join()
        employee_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    main()