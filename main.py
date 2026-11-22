import streamlit as st
import qrcode
import cv2
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image
from datetime import datetime
from pathlib import Path
import io
import os

# ==================== CONFIG ====================
EVENT_NAME = "College Tech Fest 2026"
ATTENDANCE_FILE = "attendance.csv"
QR_FOLDER = "qrcodes"
# ================================================

st.set_page_config(
    page_title="QuickPass QR | Event Check-in",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        margin-top: 0;
    }
    .stSuccess {
        background-color: #d4edda;
    }
</style>
""", unsafe_allow_html=True)

def ensure_files():
    Path(QR_FOLDER).mkdir(exist_ok=True)
    if not Path(ATTENDANCE_FILE).exists():
        pd.DataFrame(columns=["Ticket_ID", "Student_Name", "Check_In_Time"]).to_csv(ATTENDANCE_FILE, index=False)

def generate_qr(ticket_id: str, name: str):
    data = f"{ticket_id}|{name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    path = Path(QR_FOLDER) / f"{ticket_id}_{name.replace(' ', '_')}.png"
    img.save(path)
    return path, img

def mark_attendance(ticket_id: str, name: str):
    ensure_files()
    df = pd.read_csv(ATTENDANCE_FILE)
    
    if ticket_id in df["Ticket_ID"].values:
        return False, "Already Checked-In"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([[ticket_id, name, now]], columns=["Ticket_ID", "Student_Name", "Check_In_Time"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(ATTENDANCE_FILE, index=False)
    return True, now

def scan_qr_image(uploaded_file):
    image = Image.open(uploaded_file)
    decoded = decode(image)
    
    if not decoded:
        return None, None, "No QR code found in image"
    
    data = decoded[0].data.decode("utf-8")
    if "|" not in data:
        return None, None, "Invalid QR format"
    
    ticket_id, name = data.split("|", 1)
    return ticket_id.strip(), name.strip(), None

# ==================== SIDEBAR ====================
st.sidebar.title("🎫 QuickPass QR")
st.sidebar.markdown(f"**Event:** {EVENT_NAME}")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "➕ Generate QR", "✅ Check-in", "📋 Attendance", "📥 Export Report"]
)

st.sidebar.markdown("---")
st.sidebar.info("College Mini Project\nPython + Streamlit")

# ==================== PAGES ====================

ensure_files()

# ----- DASHBOARD -----
if menu == "🏠 Dashboard":
    st.markdown(f'<p class="main-header">QuickPass QR</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{EVENT_NAME} • Smart Event Check-in System</p>', unsafe_allow_html=True)
    st.markdown("---")

    df = pd.read_csv(ATTENDANCE_FILE)
    total = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checked-In", total)
    col2.metric("QR Codes Generated", len(list(Path(QR_FOLDER).glob("*.png"))))
    col3.metric("Status", "Active ✅")

    st.markdown("### How it works")
    st.markdown("""
    1. **Generate QR** → Create unique QR for each student (Ticket ID + Name)
    2. **Check-in** → Upload / scan the QR image → attendance marked automatically
    3. **View & Export** → See live list and download report
    """)

    if total > 0:
        st.markdown("### Recent Check-ins")
        st.dataframe(df.tail(5), use_container_width=True)

# ----- GENERATE QR -----
elif menu == "➕ Generate QR":
    st.header("Generate Student QR Code")
    st.markdown("Enter student details to create a unique QR code.")

    with st.form("qr_form"):
        ticket_id = st.text_input("Ticket / Roll Number", placeholder="e.g. 029")
        name = st.text_input("Student Name", placeholder="e.g. Raman Yadav")
        submitted = st.form_submit_button("Generate QR Code", type="primary")

        if submitted:
            if ticket_id.strip() and name.strip():
                path, img = generate_qr(ticket_id.strip(), name.strip())
                st.success(f"QR Generated successfully for **{name}**")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(img, caption=f"{ticket_id} - {name}", width=250)
                with col2:
                    st.code(f"File saved: {path}")
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button(
                        "Download QR",
                        data=buf.getvalue(),
                        file_name=f"{ticket_id}_{name}.png",
                        mime="image/png"
                    )
            else:
                st.error("Both Ticket ID and Name are required")

# ----- CHECK-IN -----
elif menu == "✅ Check-in":
    st.header("Student Check-in")
    st.markdown("Upload the student's QR code image to mark attendance.")

    uploaded = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

    if uploaded:
        st.image(uploaded, caption="Uploaded QR", width=250)
        
        ticket_id, name, error = scan_qr_image(uploaded)
        
        if error:
            st.error(error)
        else:
            success, result = mark_attendance(ticket_id, name)
            if success:
                st.success(f"✅ **{name}** ({ticket_id}) checked in at **{result}**")
                st.balloons()
            else:
                st.warning(f"⚠️ {name} ({ticket_id}) is already checked in")

# ----- ATTENDANCE -----
elif menu == "📋 Attendance":
    st.header("Attendance List")
    df = pd.read_csv(ATTENDANCE_FILE)

    if df.empty:
        st.info("No students have checked in yet.")
    else:
        st.metric("Total Present", len(df))
        st.dataframe(df, use_container_width=True, hide_index=True)

# ----- EXPORT -----
elif menu == "📥 Export Report":
    st.header("Export Attendance Report")
    df = pd.read_csv(ATTENDANCE_FILE)

    if df.empty:
        st.info("No data to export.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV Report",
            data=csv,
            file_name=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            type="primary"
        )

        # Text report
        report = f"""{EVENT_NAME}
Attendance Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

Ticket ID          Student Name               Check-in Time
{'-'*65}
"""
        for _, row in df.iterrows():
            report += f"{row['Ticket_ID']:<18} {row['Student_Name']:<25} {row['Check_In_Time']}\n"
        
        report += f"\n{'-'*65}\nTotal Students Checked-in: {len(df)}\n"

        st.download_button(
            "Download Text Report",
            data=report,
            file_name="attendance_report.txt",
            mime="text/plain"
        )
