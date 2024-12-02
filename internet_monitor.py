import datetime
import time
import subprocess
import csv
import os
import requests
from typing import Optional, Tuple

def check_internet():
    result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True)
    return result.returncode == 0

def measure_speed() -> Optional[float]:
    try:
        start_time = time.time()
        response = requests.get('https://www.cloudflare.com/cdn-cgi/trace', timeout=5)
        end_time = time.time()
        
        if response.status_code == 200:
            size_in_bits = len(response.content) * 8
            duration = end_time - start_time
            speed_mbps = (size_in_bits / duration) / 1_000_000
            return speed_mbps
        return None
    except Exception as e:
        print(f"Speed test failed: {e}")
        return None

def log_outage(outage_start, outage_end, filename='outage-log.csv'):
    duration = (outage_end - outage_start).total_seconds() / 60
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Outage Start', 'Outage End', 'Duration (minutes)'])
        writer.writerow([
            outage_start.strftime('%Y-%m-%d %H:%M:%S'),
            outage_end.strftime('%Y-%m-%d %H:%M:%S'),
            f'{duration:.2f}'
        ])

def log_speed_test(timestamp, speed, filename='speed-log.csv'):
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Timestamp', 'Download Speed (Mbps)'])
        writer.writerow([
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            f'{speed:.2f}'
        ])

def monitor_internet():
    print("Starting internet connection and speed monitor...")
    print(f"Logging outages to: outage-log.csv")
    print(f"Logging speed tests to: speed-log.csv")
    
    internet_was_up = True
    outage_start = None
    last_speed_test = datetime.datetime.now() - datetime.timedelta(hours=1)
    SPEED_TEST_INTERVAL = 3600  # Run speed test every hour
    
    while True:
        current_time = datetime.datetime.now()
        internet_is_up = check_internet()
        
        # Handle outage detection
        if internet_was_up and not internet_is_up:
            outage_start = current_time
            print(f"Internet outage detected at {outage_start}")
            
        elif not internet_was_up and internet_is_up and outage_start:
            outage_end = current_time
            print(f"Internet restored at {outage_end}")
            log_outage(outage_start, outage_end)
            outage_start = None
        
        # Handle speed testing
        if (internet_is_up and 
            (current_time - last_speed_test).seconds >= SPEED_TEST_INTERVAL):
            print("Running speed test...")
            speed = measure_speed()
            if speed:
                print(f"Approximate Download Speed: {speed:.2f} Mbps")
                log_speed_test(current_time, speed)
                last_speed_test = current_time
        
        internet_was_up = internet_is_up
        time.sleep(30)  # Check connectivity every 30 seconds

if __name__ == "__main__":
    try:
        monitor_internet()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")