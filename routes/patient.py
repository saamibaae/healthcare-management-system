"""
Patient routes for Flask application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from decorators import role_required
from db_utils import fetch_one, fetch_all
from models import Patient, Appointment, Bill, PharmacyBill, Pharmacy, PatientEmergencyContact, Doctor, Prescription, PrescriptionItem, Medicine

patient_bp = Blueprint('patient', __name__)


# Helper function to convert dict to model instance
def dict_to_model(model_class, data_dict):
    """Convert dictionary to model instance for template compatibility"""
    if not data_dict:
        return None
    instance = model_class()
    for key, value in data_dict.items():
        setattr(instance, key, value)
    return instance


@patient_bp.route('/dashboard')
@role_required('PATIENT')
def dashboard():
    """Patient dashboard"""
    # Get patient profile
    patient_data = fetch_one(
        "SELECT * FROM core_patient WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not patient_data:
        flash('No patient profile found for this account.', 'error')
        return render_template('patient/dashboard.html', {})
    
    patient = dict_to_model(Patient, patient_data)
    patient_id = patient_data['patient_id']
    now = datetime.now()
    
    # Emergency contacts
    emergency_contacts_data = fetch_all(
        "SELECT * FROM core_patientemergencycontact WHERE patient_id = %s AND is_primary = 1",
        (patient_id,)
    )
    emergency_contacts = [dict_to_model(PatientEmergencyContact, ec) for ec in emergency_contacts_data]
    
    # Upcoming appointments
    upcoming_appointments_data = fetch_all(
        """SELECT a.*, d.full_name as doctor_name, dept.dept_name
           FROM core_appointment a
           INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
           LEFT JOIN core_department dept ON d.dept_id = dept.dept_id
           WHERE a.patient_id = %s AND a.date_and_time >= %s
           ORDER BY a.date_and_time
           LIMIT 5""",
        (patient_id, now)
    )
    upcoming_appointments = [dict_to_model(Appointment, apt) for apt in upcoming_appointments_data]
    
    # Recent bills
    recent_bills_data = fetch_all(
        """SELECT b.*, st.name as service_type_name
           FROM core_bill b
           INNER JOIN core_servicetype st ON b.service_type_id = st.service_type_id
           WHERE b.patient_id = %s
           ORDER BY b.bill_date DESC
           LIMIT 5""",
        (patient_id,)
    )
    recent_bills = [dict_to_model(Bill, bill) for bill in recent_bills_data]
    
    context = {
        'patient': patient,
        'emergency_contacts': emergency_contacts,
        'upcoming_appointments': upcoming_appointments,
        'recent_bills': recent_bills,
    }
    
    return render_template('patient/dashboard.html', **context)


@patient_bp.route('/appointments')
@role_required('PATIENT')
def appointments():
    """List all appointments for patient"""
    # Get patient profile
    patient_data = fetch_one(
        "SELECT * FROM core_patient WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not patient_data:
        flash('No patient profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    patient = dict_to_model(Patient, patient_data)
    patient_id = patient_data['patient_id']
    
    appointments_data = fetch_all(
        """SELECT a.*, d.full_name as doctor_name, d.specialization, h.name as hospital_name
           FROM core_appointment a
           INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
           INNER JOIN core_hospital h ON d.hospital_id = h.hospital_id
           WHERE a.patient_id = %s
           ORDER BY a.date_and_time DESC""",
        (patient_id,)
    )
    appointments = [dict_to_model(Appointment, apt) for apt in appointments_data]
    
    return render_template('patient/appointments.html', appointments=appointments, patient=patient)


@patient_bp.route('/appointments/<int:appointment_id>')
@role_required('PATIENT')
def appointment_detail(appointment_id):
    """View appointment details"""
    # Get patient profile
    patient_data = fetch_one(
        "SELECT * FROM core_patient WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not patient_data:
        flash('No patient profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    patient = dict_to_model(Patient, patient_data)
    patient_id = patient_data['patient_id']
    
    # Get appointment with doctor info
    appointment_data = fetch_one(
        """SELECT a.*, d.full_name as doctor_name, d.specialization, 
                  dept.dept_name, h.name as hospital_name
           FROM core_appointment a
           INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
           LEFT JOIN core_department dept ON d.dept_id = dept.dept_id
           INNER JOIN core_hospital h ON d.hospital_id = h.hospital_id
           WHERE a.appointment_id = %s AND a.patient_id = %s""",
        (appointment_id, patient_id)
    )
    
    if not appointment_data:
        abort(404)
    
    appointment = dict_to_model(Appointment, appointment_data)
    doctor = Doctor()
    doctor.full_name = appointment_data['doctor_name']
    doctor.specialization = appointment_data['specialization']
    appointment.doctor = doctor
    
    # Get prescriptions with items
    prescriptions_data = fetch_all(
        "SELECT * FROM core_prescription WHERE appointment_id = %s",
        (appointment_id,)
    )
    
    prescriptions = []
    for presc_data in prescriptions_data:
        prescription = dict_to_model(Prescription, presc_data)
        # Get prescription items
        items_data = fetch_all(
            """SELECT pi.*, m.name as medicine_name, m.type as medicine_type
               FROM core_prescriptionitem pi
               INNER JOIN core_medicine m ON pi.medicine_id = m.medicine_id
               WHERE pi.prescription_id = %s""",
            (presc_data['prescription_id'],)
        )
        items = []
        for item_data in items_data:
            item = dict_to_model(PrescriptionItem, item_data)
            from models import Medicine
            medicine = Medicine()
            medicine.name = item_data['medicine_name']
            medicine.type = item_data['medicine_type']
            item.medicine = medicine
            items.append(item)
        prescription.items = items
        prescriptions.append(prescription)
    
    context = {
        'appointment': appointment,
        'prescriptions': prescriptions,
        'patient': patient
    }
    
    return render_template('patient/appointment_detail.html', **context)


@patient_bp.route('/bills')
@role_required('PATIENT')
def bills():
    """View all bills"""
    # Get patient profile
    patient_data = fetch_one(
        "SELECT * FROM core_patient WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not patient_data:
        flash('No patient profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    patient = dict_to_model(Patient, patient_data)
    patient_id = patient_data['patient_id']
    
    # Get all bills
    bills_data = fetch_all(
        """SELECT b.*, st.name as service_type_name
           FROM core_bill b
           INNER JOIN core_servicetype st ON b.service_type_id = st.service_type_id
           WHERE b.patient_id = %s
           ORDER BY b.bill_date DESC""",
        (patient_id,)
    )
    bills = [dict_to_model(Bill, bill) for bill in bills_data]
    
    # Get pharmacy bills with JOINs
    pharmacy_bills_data = fetch_all(
        """SELECT pb.*, b.*, p.name as pharmacy_name
           FROM core_pharmacybill pb
           INNER JOIN core_bill b ON pb.bill_id = b.bill_id
           INNER JOIN core_pharmacy p ON pb.pharmacy_id = p.pharmacy_id
           WHERE b.patient_id = %s
           ORDER BY pb.purchase_date DESC""",
        (patient_id,)
    )
    
    pharmacy_bills = []
    for pb_data in pharmacy_bills_data:
        pb = dict_to_model(PharmacyBill, pb_data)
        bill = dict_to_model(Bill, pb_data)
        pharmacy = Pharmacy()
        pharmacy.name = pb_data['pharmacy_name']
        pb.bill = bill
        pb.pharmacy = pharmacy
        pharmacy_bills.append(pb)
    
    context = {
        'bills': bills,
        'pharmacy_bills': pharmacy_bills,
        'patient': patient
    }
    
    return render_template('patient/bills.html', **context)


@patient_bp.route('/profile')
@role_required('PATIENT')
def profile():
    """View patient profile"""
    # Get patient profile
    patient_data = fetch_one(
        "SELECT * FROM core_patient WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not patient_data:
        flash('No patient profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    patient = dict_to_model(Patient, patient_data)
    patient_id = patient_data['patient_id']
    
    # Get emergency contacts
    emergency_contacts_data = fetch_all(
        "SELECT * FROM core_patientemergencycontact WHERE patient_id = %s",
        (patient_id,)
    )
    emergency_contacts = [dict_to_model(PatientEmergencyContact, ec) for ec in emergency_contacts_data]
    
    context = {
        'patient': patient,
        'emergency_contacts': emergency_contacts
    }
    
    return render_template('patient/profile.html', **context)

