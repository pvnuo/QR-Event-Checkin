"""
QR Code Based Event Check-in System
College Mini Project - Python
Easy to explain: Generate QR → Scan → Mark attendance → Save in CSV
"""

import csv
import os
from datetime import datetime
from pathlib import Path

import cv2
import qrcode
from pyzbar.pyzbar import decode
from PIL import Image

# ==================== CONFIG ====================
EVENT_NAME = "College Tech Fest 2026"
ATTENDANCE_FILE = "attendance.csv"
QR_FOLDER = "qrcodes"
# ================================================

def ensure_files():
    """Create necessary folders and CSV file if they don't exist"""
    Path(QR_FOLDER).mkdir(exist_ok=True)
    if not Path(ATTENDANCE_FILE).exists():
        with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Ticket_ID", "Student_Name", "Check_In_Time"])

def generate_qr(ticket_id: str, name: str):
    """
    Generate a QR code that stores: TicketID|StudentName
    This QR will be scanned later for check-in
    """
    data = f"{ticket_id}|{name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    path = Path(QR_FOLDER) / f"{ticket_id}_{name.replace(' ', '_')}.png"
    img.save(path)
    print(f"[+] QR Generated → {path}")
    return path

def mark_attendance(ticket_id: str, name: str):
    """
    Mark student as present.
    Prevents double check-in of the same ticket.
    """
    ensure_files()
    
    # Check if already present
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Ticket_ID"] == ticket_id:
                print(f"[!] Already Checked-In: {name} at {row['Check_In_Time']}")
                return False

    # New check-in
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ATTENDANCE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ticket_id, name, now])
    
    print(f"[✓] SUCCESS: {name} ({ticket_id}) checked in at {now}")
    return True

def scan_from_camera():
    """Open webcam and continuously scan for QR codes"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Camera not found / permission denied")
        return

    print("[*] Camera started. Show QR code. Press 'Q' to stop.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Decode any QR in the frame
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            data = obj.data.decode("utf-8")
            if "|" in data:
                ticket_id, name = data.split("|", 1)
                mark_attendance(ticket_id.strip(), name.strip())
                
                # Draw green box around QR
                points = obj.polygon
                if len(points) > 2:
                    for i in range(len(points)):
                        cv2.line(frame, points[i], points[(i + 1) % len(points)], (0, 255, 0), 3)

        cv2.imshow("QR Event Check-in - Press Q to Exit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

def scan_from_image(image_path: str):
    """Scan QR code from a saved image file (useful for testing)"""
    if not os.path.isfile(image_path):
        print("[!] Image file not found")
        return

    img = Image.open(image_path)
    decoded = decode(img)
    
    if not decoded:
        print("[!] No QR code found in this image")
        return

    for obj in decoded:
        data = obj.data.decode("utf-8")
        if "|" in data:
            ticket_id, name = data.split("|", 1)
            mark_attendance(ticket_id.strip(), name.strip())
        else:
            print(f"[!] Invalid QR format: {data}")

def show_attendance():
    """Display all checked-in students"""
    ensure_files()
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if len(rows) <= 1:
        print("\nNo one has checked in yet.\n")
        return

    print(f"\n{'='*50}")
    print(f"  {EVENT_NAME} - Attendance List")
    print(f"{'='*50}")
    print(f"{'Ticket':<12} {'Name':<20} {'Time'}")
    print("-" * 50)
    
    for row in rows[1:]:  # skip header
        print(f"{row[0]:<12} {row[1]:<20} {row[2]}")
    
    print("-" * 50)
    print(f"Total Present: {len(rows)-1}")
    print(f"{'='*50}\n")

def export_report():
    """Create a simple text report for submission"""
    ensure_files()
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    report_file = "attendance_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"{EVENT_NAME}\n")
        f.write(f"Attendance Report\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        
        if len(rows) <= 1:
            f.write("No attendance recorded.\n")
        else:
            f.write(f"{'Ticket ID':<15} {'Student Name':<25} {'Check-in Time'}\n")
            f.write("-"*65 + "\n")
            for row in rows[1:]:
                f.write(f"{row[0]:<15} {row[1]:<25} {row[2]}\n")
            f.write("\n" + "-"*65 + "\n")
            f.write(f"Total Students Checked-in: {len(rows)-1}\n")

    print(f"[+] Report saved as → {report_file}")

def main_menu():
    ensure_files()
    while True:
        print(f"""
╔════════════════════════════════════════════╗
║     {EVENT_NAME:<34} ║
║          QR Code Event Check-in            ║
╠════════════════════════════════════════════╣
║  1. Generate QR for a student              ║
║  2. Scan QR using Camera                   ║
║  3. Scan QR from Image file                ║
║  4. View Attendance List                   ║
║  5. Export Attendance Report               ║
║  6. Exit                                   ║
╚════════════════════════════════════════════╝
""")
        choice = input("Enter your choice (1-6) → ").strip()

        if choice == "1":
            print("\n--- Generate QR ---")
            tid = input("Enter Ticket / Roll No : ").strip()
            name = input("Enter Student Name    : ").strip()
            if tid and name:
                generate_qr(tid, name)
            else:
                print("[!] Both Ticket ID and Name are required")

        elif choice == "2":
            scan_from_camera()

        elif choice == "3":
            path = input("Enter full path of image → ").strip()
            scan_from_image(path)

        elif choice == "4":
            show_attendance()

        elif choice == "5":
            export_report()

        elif choice == "6":
            print("\nThank you! Project closed.")
            break

        else:
            print("[!] Invalid choice. Please enter 1 to 6.")

if __name__ == "__main__":
    main_menu()