#!/usr/bin/env python3
"""
Provide statistics about Nginx logs stored in MongoDB.
Database: logs, Collection: nginx.
First line: Number of logs in the collection.
Second line: Method counts for GET, POST, PUT, PATCH, DELETE.
Final line: Count of GET requests with the path '/status'.
"""

from pymongo import MongoClient

HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

def display_log_statistics(collection, method_filter=None):
    """
    Display statistics about Nginx logs stored in the specified MongoDB collection.
    
    Args:
        collection: The MongoDB collection containing the Nginx logs.
        method_filter: An optional HTTP method to filter the logs by.
    """
    if method_filter:
        method_count = collection.count_documents({"method": method_filter})
        print(f"\tmethod {method_filter}: {method_count}")
        return

    total_logs = collection.count_documents({})
    print(f"{total_logs} logs")
    print("Methods:")
    for method in HTTP_METHODS:
        display_log_statistics(collection, method)

    status_check_count = collection.count_documents({"method": "GET", "path": "/status"})
    print(f"{status_check_count} status check")

if __name__ == "__main__":
    client = MongoClient('mongodb://127.0.0.1:27017')
    nginx_logs_collection = client.logs.nginx
    display_log_statistics(nginx_logs_collection)
