"""
Doctor routes for Flask application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from decimal import Decimal
from decorators import role_required
from forms import AppointmentUpdateForm, PrescriptionForm, PrescriptionItemForm, LabTestForm, LabTestUpdateForm
from db_utils import fetch_one, fetch_all, fetch_count, execute_insert, execute_update
from models import Doctor, Appointment, Patient, Prescription, PrescriptionItem, Medicine, LabTest, Lab

doctor_bp = Blueprint('doctor', __name__)


# Helper function to convert dict to model instance
def dict_to_model(model_class, data_dict):
    """Convert dictionary to model instance for template compatibility"""
    if not data_dict:
        return None
    instance = model_class()
    for key, value in data_dict.items():
        setattr(instance, key, value)
    return instance


@doctor_bp.route('/dashboard')
@role_required('DOCTOR')
def dashboard():
    """Doctor dashboard"""
    # Get doctor profile using raw SQL
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found for this account.', 'error')
        return render_template('doctor/dashboard.html', {})
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    today = date.today()
    now = datetime.now()
    
    # Today's appointments
    today_appointments_data = fetch_all(
        """SELECT a.*, p.full_name as patient_name
           FROM core_appointment a
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE a.doctor_id = %s AND DATE(a.date_and_time) = %s
           ORDER BY a.date_and_time""",
        (doctor_id, today)
    )
    today_appointments = [dict_to_model(Appointment, apt) for apt in today_appointments_data]
    
    # Upcoming appointments
    upcoming_appointments_data = fetch_all(
        """SELECT a.*, p.full_name as patient_name
           FROM core_appointment a
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE a.doctor_id = %s AND a.date_and_time > %s AND a.status = 'Scheduled'
           ORDER BY a.date_and_time
           LIMIT 10""",
        (doctor_id, now)
    )
    upcoming_appointments = [dict_to_model(Appointment, apt) for apt in upcoming_appointments_data]
    
    # Recent completed appointments
    completed_appointments_data = fetch_all(
        """SELECT a.*, p.full_name as patient_name
           FROM core_appointment a
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE a.doctor_id = %s AND a.status = 'Completed'
           ORDER BY a.date_and_time DESC
           LIMIT 5""",
        (doctor_id,)
    )
    completed_appointments = [dict_to_model(Appointment, apt) for apt in completed_appointments_data]
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
    }
    
    return render_template('doctor/dashboard.html', **context)


@doctor_bp.route('/appointments')
@role_required('DOCTOR')
def appointments():
    """List all appointments for doctor"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    
    # Build query with optional status filter
    status = request.args.get('status')
    if status:
        appointments_data = fetch_all(
            """SELECT a.*, p.full_name as patient_name
               FROM core_appointment a
               INNER JOIN core_patient p ON a.patient_id = p.patient_id
               WHERE a.doctor_id = %s AND a.status = %s
               ORDER BY a.date_and_time DESC""",
            (doctor_id, status)
        )
    else:
        appointments_data = fetch_all(
            """SELECT a.*, p.full_name as patient_name
               FROM core_appointment a
               INNER JOIN core_patient p ON a.patient_id = p.patient_id
               WHERE a.doctor_id = %s
               ORDER BY a.date_and_time DESC""",
            (doctor_id,)
        )
    
    appointments = [dict_to_model(Appointment, apt) for apt in appointments_data]
    
    return render_template('doctor/appointments.html', appointments=appointments, doctor=doctor)


@doctor_bp.route('/appointments/<int:appointment_id>', methods=['GET', 'POST'])
@role_required('DOCTOR')
def appointment_detail(appointment_id):
    """View and update appointment details"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    
    # Get appointment with patient info
    appointment_data = fetch_one(
        """SELECT a.*, p.*, p.patient_id as patient_pk
           FROM core_appointment a
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE a.appointment_id = %s AND a.doctor_id = %s""",
        (appointment_id, doctor_id)
    )
    
    if not appointment_data:
        abort(404)
    
    appointment = dict_to_model(Appointment, appointment_data)
    patient = dict_to_model(Patient, appointment_data)
    appointment.patient = patient
    
    form = AppointmentUpdateForm()
    if form.validate_on_submit():
        # Update appointment using raw SQL
        sql = """UPDATE core_appointment 
                 SET status = %s, diagnosis = %s, follow_up_date = %s
                 WHERE appointment_id = %s"""
        execute_update(sql, (
            form.status.data,
            form.diagnosis.data or None,
            form.follow_up_date.data or None,
            appointment_id
        ))
        flash('Appointment updated successfully.', 'success')
        return redirect(url_for('doctor.appointment_detail', appointment_id=appointment_id))
    else:
        # Populate form with existing data
        form.status.data = appointment_data['status']
        form.diagnosis.data = appointment_data.get('diagnosis', '')
        form.follow_up_date.data = appointment_data.get('follow_up_date')
    
    # Get prescriptions with items
    prescriptions_data = fetch_all(
        """SELECT p.* FROM core_prescription p
           WHERE p.appointment_id = %s""",
        (appointment_id,)
    )
    
    prescriptions = []
    for presc_data in prescriptions_data:
        prescription = dict_to_model(Prescription, presc_data)
        # Get prescription items with medicine info
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
            medicine = Medicine()
            medicine.name = item_data['medicine_name']
            medicine.type = item_data['medicine_type']
            item.medicine = medicine
            items.append(item)
        prescription.items = items
        prescriptions.append(prescription)
    
    context = {
        'appointment': appointment,
        'form': form,
        'prescriptions': prescriptions,
        'doctor': doctor
    }
    
    return render_template('doctor/appointment_detail.html', **context)


@doctor_bp.route('/appointments/<int:appointment_id>/prescription/create', methods=['GET', 'POST'])
@role_required('DOCTOR')
def create_prescription(appointment_id):
    """Create prescription for appointment"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    
    # Get appointment
    appointment_data = fetch_one(
        """SELECT a.*, p.full_name as patient_name
           FROM core_appointment a
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE a.appointment_id = %s AND a.doctor_id = %s""",
        (appointment_id, doctor_id)
    )
    
    if not appointment_data:
        abort(404)
    
    appointment = dict_to_model(Appointment, appointment_data)
    
    form = PrescriptionForm()
    if form.validate_on_submit():
        # Insert prescription using raw SQL
        sql = """INSERT INTO core_prescription (appointment_id, valid_until, refill_count, notes)
                 VALUES (%s, %s, %s, %s)"""
        prescription_id = execute_insert(sql, (
            appointment_id,
            form.valid_until.data,
            form.refill_count.data or 0,
            form.notes.data or ''
        ))
        flash('Prescription created successfully. Now add medicines.', 'success')
        return redirect(url_for('doctor.add_prescription_items', prescription_id=prescription_id))
    else:
        # Set default valid_until to 30 days from now
        form.valid_until.data = date.today() + timedelta(days=30)
    
    return render_template('doctor/prescription_form.html', form=form, appointment=appointment)


@doctor_bp.route('/prescription/<int:prescription_id>/add-items', methods=['GET', 'POST'])
@role_required('DOCTOR')
def add_prescription_items(prescription_id):
    """Add items to prescription"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    
    # Get prescription with appointment check
    prescription_data = fetch_one(
        """SELECT p.*, a.doctor_id
           FROM core_prescription p
           INNER JOIN core_appointment a ON p.appointment_id = a.appointment_id
           WHERE p.prescription_id = %s AND a.doctor_id = %s""",
        (prescription_id, doctor_id)
    )
    
    if not prescription_data:
        abort(404)
    
    prescription = dict_to_model(Prescription, prescription_data)
    
    # Get existing items
    existing_items_data = fetch_all(
        """SELECT pi.*, m.name as medicine_name, m.type as medicine_type
           FROM core_prescriptionitem pi
           INNER JOIN core_medicine m ON pi.medicine_id = m.medicine_id
           WHERE pi.prescription_id = %s""",
        (prescription_id,)
    )
    
    existing_items = []
    for item_data in existing_items_data:
        item = dict_to_model(PrescriptionItem, item_data)
        medicine = Medicine()
        medicine.name = item_data['medicine_name']
        medicine.type = item_data['medicine_type']
        item.medicine = medicine
        existing_items.append(item)
    
    # Get medicines for form
    medicines_data = fetch_all("SELECT * FROM core_medicine ORDER BY name")
    form = PrescriptionItemForm()
    form.medicine.choices = [(m['medicine_id'], m['name']) for m in medicines_data]
    
    if form.validate_on_submit():
        # Insert prescription item using raw SQL
        medicine_id = form.medicine.data
        sql = """INSERT INTO core_prescriptionitem 
                 (prescription_id, medicine_id, dosage, frequency, duration, quantity, 
                  before_after_meal, instructions)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        execute_insert(sql, (
            prescription_id,
            medicine_id,
            form.dosage.data,
            form.frequency.data,
            form.duration.data,
            form.quantity.data,
            form.before_after_meal.data,
            form.instructions.data or ''
        ))
        # Get medicine name for flash message
        medicine_data = fetch_one("SELECT name FROM core_medicine WHERE medicine_id = %s", (medicine_id,))
        medicine_name = medicine_data['name'] if medicine_data else 'Medicine'
        flash(f'Added {medicine_name} to prescription.', 'success')
        return redirect(url_for('doctor.add_prescription_items', prescription_id=prescription_id))
    
    context = {
        'form': form,
        'prescription': prescription,
        'existing_items': existing_items,
    }
    
    return render_template('doctor/add_prescription_items.html', **context)


@doctor_bp.route('/lab-test/order', methods=['GET', 'POST'])
@role_required('DOCTOR')
def order_lab_test():
    """Order lab test"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    hospital_id = doctor_data['hospital_id']
    
    # Get labs for doctor's hospital
    labs_data = fetch_all(
        "SELECT * FROM core_lab WHERE hospital_id = %s",
        (hospital_id,)
    )
    
    # Get patients for form
    patients_data = fetch_all("SELECT * FROM core_patient ORDER BY full_name")
    
    form = LabTestForm()
    form.lab.choices = [(lab['lab_id'], lab['lab_name']) for lab in labs_data]
    form.patient.choices = [(p['patient_id'], p['full_name']) for p in patients_data]
    
    if form.validate_on_submit():
        # Insert lab test using raw SQL
        lab_id = form.lab.data
        patient_id = form.patient.data
        sql = """INSERT INTO core_labtest 
                 (lab_id, patient_id, test_type, ordered_by_id, remarks, test_cost, status)
                 VALUES (%s, %s, %s, %s, %s, %s, 'Ordered')"""
        execute_insert(sql, (
            lab_id,
            patient_id,
            form.test_type.data,
            doctor_id,
            form.remarks.data or '',
            form.test_cost.data
        ))
        flash(f'Lab test "{form.test_type.data}" ordered successfully.', 'success')
        return redirect(url_for('doctor.dashboard'))
    
    return render_template('doctor/lab_test_form.html', form=form, doctor=doctor)


@doctor_bp.route('/lab-test/<int:test_id>/update', methods=['GET', 'POST'])
@role_required('DOCTOR')
def update_lab_test(test_id):
    """Update lab test status and result - triggers auto-billing when completed"""
    # Get doctor profile
    doctor_data = fetch_one(
        "SELECT * FROM core_doctor WHERE user_id = %s",
        (current_user.id,)
    )
    
    if not doctor_data:
        flash('No doctor profile found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    doctor = dict_to_model(Doctor, doctor_data)
    doctor_id = doctor_data['doctor_id']
    
    # Get lab test with doctor check
    lab_test_data = fetch_one(
        "SELECT * FROM core_labtest WHERE test_id = %s AND ordered_by_id = %s",
        (test_id, doctor_id)
    )
    
    if not lab_test_data:
        abort(404)
    
    old_status = lab_test_data['status']
    
    form = LabTestUpdateForm()
    if form.validate_on_submit():
        new_status = form.status.data
        result = form.result.data or None
        
        # Update lab test using raw SQL
        sql = """UPDATE core_labtest 
                 SET status = %s, result = %s
                 WHERE test_id = %s"""
        execute_update(sql, (new_status, result, test_id))
        
        # Auto-billing: If status changed to 'Completed', create bill
        if old_status != 'Completed' and new_status == 'Completed':
            from datetime import timedelta
            from db_utils import get_or_create
            
            patient_id = lab_test_data['patient_id']
            test_cost = lab_test_data['test_cost']
            transaction_id = f'LAB-{test_id}'
            
            # Check if bill already exists using raw SQL
            existing_bill = fetch_count(
                """SELECT COUNT(*) FROM core_bill b
                   INNER JOIN core_servicetype st ON b.service_type_id = st.service_type_id
                   WHERE b.patient_id = %s AND st.name = 'Laboratory' AND b.transaction_id = %s""",
                (patient_id, transaction_id)
            ) > 0
            
            if not existing_bill:
                # Get or create Laboratory service type using raw SQL
                lab_service_data, _ = get_or_create(
                    'core_servicetype',
                    {'name': 'Laboratory'},
                    {'description': 'Lab test services'}
                )
                
                service_type_id = lab_service_data['service_type_id']
                
                # Create bill using raw SQL
                due_date = date.today() + timedelta(days=30)
                bill_sql = """INSERT INTO core_bill 
                             (patient_id, service_type_id, total_amount, status, due_date, transaction_id, bill_date)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                execute_insert(bill_sql, (
                    patient_id,
                    service_type_id,
                    test_cost,
                    'Pending',
                    due_date,
                    transaction_id,
                    date.today()
                ))
                flash('Lab test updated and bill created automatically.', 'success')
            else:
                flash('Lab test updated. Bill already exists.', 'info')
        else:
            flash('Lab test updated successfully.', 'success')
        
        return redirect(url_for('doctor.dashboard'))
    else:
        # Populate form with existing data
        form.status.data = lab_test_data['status']
        form.result.data = lab_test_data.get('result', '')
    
    lab_test = dict_to_model(LabTest, lab_test_data)
    return render_template('doctor/lab_test_update.html', form=form, lab_test=lab_test, doctor=doctor)

