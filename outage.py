import datetime
import time
import subprocess
import csv
import os
import speedtest
from typing import Optional, Tuple

def check_internet():
    result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True)
    return result.returncode == 0

def measure_speed() -> Optional[Tuple[float, float]]:
    try:
        st = speedtest.Speedtest()
        print("Testing download speed...")
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        print("Testing upload speed...")
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        return (download_speed, upload_speed)
    except Exception as e:
        print(f"Speed test failed: {e}")
        return None

def log_data(timestamp, is_outage=False, outage_end=None, duration=None, 
             download_speed=None, upload_speed=None, 
             filename='internet_monitor.csv'):
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                'Timestamp', 
                'Event Type',
                'Outage End', 
                'Outage Duration (min)',
                'Download Speed (Mbps)',
                'Upload Speed (Mbps)'
            ])
        writer.writerow([
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Outage' if is_outage else 'Speed Test',
            outage_end.strftime('%Y-%m-%d %H:%M:%S') if outage_end else '',
            f'{duration:.2f}' if duration else '',
            f'{download_speed:.2f}' if download_speed else '',
            f'{upload_speed:.2f}' if upload_speed else ''
        ])

def monitor_internet():
    print("Starting internet connection and speed monitor...")
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
            log_data(outage_start, is_outage=True)
            
        elif not internet_was_up and internet_is_up and outage_start:
            outage_end = current_time
            duration = (outage_end - outage_start).total_seconds() / 60
            print(f"Internet restored at {outage_end}")
            log_data(outage_start, is_outage=True, outage_end=outage_end, duration=duration)
            outage_start = None
        
        # Handle speed testing
        if (internet_is_up and 
            (current_time - last_speed_test).seconds >= SPEED_TEST_INTERVAL):
            print("Running speed test...")
            speeds = measure_speed()
            if speeds:
                download_speed, upload_speed = speeds
                print(f"Download: {download_speed:.2f} Mbps")
                print(f"Upload: {upload_speed:.2f} Mbps")
                log_data(current_time, download_speed=download_speed, upload_speed=upload_speed)
                last_speed_test = current_time
        
        internet_was_up = internet_is_up
        time.sleep(30)  # Check connectivity every 30 seconds

if __name__ == "__main__":
    try:
        monitor_internet()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")