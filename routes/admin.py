"""
Hospital Admin routes for Flask application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from decimal import Decimal
from decorators import role_required
from forms import DepartmentForm, LabForm, DoctorCreationForm, PharmacyStockUpdateForm
from db_utils import fetch_one, fetch_all, fetch_count, execute_insert, execute_update
from models import Department, Lab, Doctor, Pharmacy, PharmacyMedicine, Medicine, Hospital, Appointment
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)


# Helper function to convert dict to model instance
def dict_to_model(model_class, data_dict):
    """Convert dictionary to model instance for template compatibility"""
    if not data_dict:
        return None
    instance = model_class()
    for key, value in data_dict.items():
        setattr(instance, key, value)
    return instance


@admin_bp.route('/dashboard')
@role_required('ADMIN')
def dashboard():
    """Hospital admin dashboard"""
    hospital = current_user.hospital
    
    if not hospital:
        flash('No hospital assigned to this admin account.', 'error')
        return render_template('admin/dashboard.html', {})
    
    hospital_id = hospital.hospital_id
    today = date.today()
    
    # Get statistics using raw SQL
    departments_count = fetch_count(
        "SELECT COUNT(*) FROM core_department WHERE hospital_id = %s",
        (hospital_id,)
    )
    
    doctors_count = fetch_count(
        "SELECT COUNT(*) FROM core_doctor WHERE hospital_id = %s",
        (hospital_id,)
    )
    
    labs_count = fetch_count(
        "SELECT COUNT(*) FROM core_lab WHERE hospital_id = %s",
        (hospital_id,)
    )
    
    # Today's appointments
    today_appointments = fetch_count(
        """SELECT COUNT(*) FROM core_appointment a
           INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
           WHERE d.hospital_id = %s AND DATE(a.date_and_time) = %s""",
        (hospital_id, today)
    )
    
    # Recent appointments with JOINs
    recent_appointments_data = fetch_all(
        """SELECT a.*, d.full_name as doctor_name, p.full_name as patient_name
           FROM core_appointment a
           INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
           INNER JOIN core_patient p ON a.patient_id = p.patient_id
           WHERE d.hospital_id = %s
           ORDER BY a.date_and_time DESC
           LIMIT 10""",
        (hospital_id,)
    )
    
    # Convert to model-like objects for template compatibility
    recent_appointments = [dict_to_model(Appointment, apt) for apt in recent_appointments_data]
    
    # Appointments per day for last 7 days (for chart)
    appointments_data = []
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        count = fetch_count(
            """SELECT COUNT(*) FROM core_appointment a
               INNER JOIN core_doctor d ON a.doctor_id = d.doctor_id
               WHERE d.hospital_id = %s AND DATE(a.date_and_time) = %s""",
            (hospital_id, day_date)
        )
        appointments_data.append({
            'date': day_date.strftime('%b %d'),
            'count': count
        })
    
    context = {
        'hospital': hospital,
        'departments_count': departments_count,
        'doctors_count': doctors_count,
        'labs_count': labs_count,
        'today_appointments': today_appointments,
        'recent_appointments': recent_appointments,
        'appointments_data': appointments_data,
    }
    
    return render_template('admin/dashboard.html', **context)


@admin_bp.route('/departments')
@role_required('ADMIN')
def departments():
    """List all departments"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    departments_data = fetch_all(
        "SELECT * FROM core_department WHERE hospital_id = %s ORDER BY dept_name",
        (hospital_id,)
    )
    departments = [dict_to_model(Department, dept) for dept in departments_data]
    
    return render_template('admin/departments.html', departments=departments, hospital=hospital)


@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@role_required('ADMIN')
def department_add():
    """Add new department"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    form = DepartmentForm()
    if form.validate_on_submit():
        # Insert using raw SQL
        sql = """INSERT INTO core_department (dept_name, hospital_id, floor, extension, operating_hours)
                 VALUES (%s, %s, %s, %s, %s)"""
        execute_insert(sql, (
            form.dept_name.data,
            hospital_id,
            form.floor.data,
            form.extension.data or None,
            form.operating_hours.data
        ))
        flash(f'Department "{form.dept_name.data}" added successfully.', 'success')
        return redirect(url_for('admin.departments'))
    
    return render_template('admin/department_form.html', form=form, title='Add Department')


@admin_bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@role_required('ADMIN')
def department_edit(dept_id):
    """Edit department"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    # Get department using raw SQL
    department_data = fetch_one(
        "SELECT * FROM core_department WHERE dept_id = %s AND hospital_id = %s",
        (dept_id, hospital_id)
    )
    
    if not department_data:
        abort(404)
    
    department = dict_to_model(Department, department_data)
    
    form = DepartmentForm()
    if form.validate_on_submit():
        # Update using raw SQL
        sql = """UPDATE core_department 
                 SET dept_name = %s, floor = %s, extension = %s, operating_hours = %s
                 WHERE dept_id = %s"""
        execute_update(sql, (
            form.dept_name.data,
            form.floor.data,
            form.extension.data or None,
            form.operating_hours.data,
            dept_id
        ))
        flash(f'Department "{form.dept_name.data}" updated successfully.', 'success')
        return redirect(url_for('admin.departments'))
    else:
        # Populate form with existing data
        form.dept_name.data = department_data['dept_name']
        form.floor.data = department_data['floor']
        form.extension.data = department_data.get('extension')
        form.operating_hours.data = department_data['operating_hours']
    
    return render_template('admin/department_form.html', form=form, title='Edit Department')


@admin_bp.route('/labs')
@role_required('ADMIN')
def labs():
    """List all labs"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    labs_data = fetch_all(
        "SELECT * FROM core_lab WHERE hospital_id = %s ORDER BY lab_name",
        (hospital_id,)
    )
    labs = [dict_to_model(Lab, lab) for lab in labs_data]
    
    return render_template('admin/labs.html', labs=labs, hospital=hospital)


@admin_bp.route('/labs/add', methods=['GET', 'POST'])
@role_required('ADMIN')
def lab_add():
    """Add new lab"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    form = LabForm()
    if form.validate_on_submit():
        # Insert using raw SQL
        sql = """INSERT INTO core_lab (lab_name, hospital_id, location, phone)
                 VALUES (%s, %s, %s, %s)"""
        execute_insert(sql, (
            form.lab_name.data,
            hospital_id,
            form.location.data,
            form.phone.data
        ))
        flash(f'Lab "{form.lab_name.data}" added successfully.', 'success')
        return redirect(url_for('admin.labs'))
    
    return render_template('admin/lab_form.html', form=form, title='Add Lab')


@admin_bp.route('/doctors')
@role_required('ADMIN')
def doctors():
    """List all doctors"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    # Get doctors with department info using JOIN
    doctors_data = fetch_all(
        """SELECT d.*, dept.dept_name as dept_name
           FROM core_doctor d
           LEFT JOIN core_department dept ON d.dept_id = dept.dept_id
           WHERE d.hospital_id = %s
           ORDER BY d.full_name""",
        (hospital_id,)
    )
    
    # Convert to model-like objects
    doctors = []
    for doc_data in doctors_data:
        doctor = dict_to_model(Doctor, doc_data)
        if doc_data.get('dept_name'):
            # Create a minimal dept object for template
            dept = Department()
            dept.dept_name = doc_data['dept_name']
            doctor.dept = dept
        doctors.append(doctor)
    
    return render_template('admin/doctors.html', doctors=doctors, hospital=hospital)


@admin_bp.route('/doctors/add', methods=['GET', 'POST'])
@role_required('ADMIN')
def doctor_add():
    """Add new doctor"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    # Get departments for this hospital
    departments_data = fetch_all(
        "SELECT * FROM core_department WHERE hospital_id = %s",
        (hospital_id,)
    )
    
    form = DoctorCreationForm()
    # Populate department choices
    form.dept.choices = [('', '---------')] + [(dept['dept_id'], dept['dept_name']) for dept in departments_data]
    
    if form.validate_on_submit():
        # Check if username exists
        existing_user = fetch_one(
            "SELECT id FROM core_customuser WHERE username = %s",
            (form.username.data,)
        )
        if existing_user:
            flash('Username already exists.', 'error')
            return render_template('admin/doctor_form.html', form=form, title='Add Doctor')
        
        # Check if license_no exists
        existing_doctor = fetch_one(
            "SELECT doctor_id FROM core_doctor WHERE license_no = %s",
            (form.license_no.data,)
        )
        if existing_doctor:
            flash('License number already exists.', 'error')
            return render_template('admin/doctor_form.html', form=form, title='Add Doctor')
        
        # Create user account
        hashed_password = generate_password_hash(form.password.data)
        user_sql = """INSERT INTO core_customuser 
                     (username, password, email, first_name, last_name, is_active, 
                      is_staff, is_superuser, date_joined, role, hospital_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        # Split full_name into first and last
        name_parts = form.full_name.data.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user_id = execute_insert(
            user_sql,
            (form.username.data, hashed_password, form.email.data, first_name, last_name,
             True, False, False, datetime.utcnow(), 'DOCTOR', hospital_id)
        )
        
        # Insert doctor using raw SQL
        sql = """INSERT INTO core_doctor 
                 (license_no, full_name, specialization, phone, email, experience_yrs, 
                  gender, shift_timing, join_date, hospital_id, dept_id, user_id)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        dept_id = form.dept.data if form.dept.data else None
        
        doctor_id = execute_insert(sql, (
            form.license_no.data,
            form.full_name.data,
            form.specialization.data,
            form.phone.data,
            form.email.data,
            form.experience_yrs.data,
            form.gender.data,
            form.shift_timing.data,
            form.join_date.data,
            hospital_id,
            dept_id,
            user_id
        ))
        
        flash(f'Doctor "{form.full_name.data}" added successfully.', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/doctor_form.html', form=form, title='Add Doctor')


@admin_bp.route('/pharmacy/stock')
@role_required('ADMIN')
def pharmacy_stock():
    """View and manage pharmacy stock"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    # Get pharmacies for this hospital
    pharmacies_data = fetch_all(
        "SELECT * FROM core_pharmacy WHERE hospital_id = %s",
        (hospital_id,)
    )
    pharmacies = [dict_to_model(Pharmacy, pharm) for pharm in pharmacies_data]
    
    # Get pharmacy from request or first pharmacy
    pharmacy_id = request.args.get('pharmacy')
    selected_pharmacy = None
    stock_items = []
    
    if pharmacy_id:
        pharmacy_data = fetch_one(
            "SELECT * FROM core_pharmacy WHERE pharmacy_id = %s AND hospital_id = %s",
            (pharmacy_id, hospital_id)
        )
        if pharmacy_data:
            selected_pharmacy = dict_to_model(Pharmacy, pharmacy_data)
    elif pharmacies_data:
        selected_pharmacy = dict_to_model(Pharmacy, pharmacies_data[0])
    
    if selected_pharmacy:
        # Get stock items with medicine info using JOIN
        stock_items_data = fetch_all(
            """SELECT pm.*, m.name as medicine_name, m.type as medicine_type
               FROM core_pharmacymedicine pm
               INNER JOIN core_medicine m ON pm.medicine_id = m.medicine_id
               WHERE pm.pharmacy_id = %s
               ORDER BY m.name""",
            (selected_pharmacy.pharmacy_id,)
        )
        
        # Convert to model-like objects
        for item_data in stock_items_data:
            item = dict_to_model(PharmacyMedicine, item_data)
            medicine = Medicine()
            medicine.name = item_data['medicine_name']
            medicine.type = item_data['medicine_type']
            item.medicine = medicine
            stock_items.append(item)
    
    context = {
        'pharmacies': pharmacies,
        'selected_pharmacy': selected_pharmacy,
        'stock_items': stock_items,
        'hospital': hospital
    }
    
    return render_template('admin/pharmacy_stock.html', **context)


@admin_bp.route('/pharmacy/stock/<int:stock_id>/update', methods=['GET', 'POST'])
@role_required('ADMIN')
def pharmacy_stock_update(stock_id):
    """Update pharmacy stock"""
    hospital = current_user.hospital
    hospital_id = hospital.hospital_id
    
    # Get stock item with pharmacy check
    stock_item_data = fetch_one(
        """SELECT pm.*, p.hospital_id
           FROM core_pharmacymedicine pm
           INNER JOIN core_pharmacy p ON pm.pharmacy_id = p.pharmacy_id
           WHERE pm.pharmacy_medicine_id = %s AND p.hospital_id = %s""",
        (stock_id, hospital_id)
    )
    
    if not stock_item_data:
        abort(404)
    
    stock_item = dict_to_model(PharmacyMedicine, stock_item_data)
    
    # Get medicine info
    medicine_data = fetch_one(
        "SELECT * FROM core_medicine WHERE medicine_id = %s",
        (stock_item_data['medicine_id'],)
    )
    if medicine_data:
        stock_item.medicine = dict_to_model(Medicine, medicine_data)
    
    form = PharmacyStockUpdateForm()
    if form.validate_on_submit():
        # Update using raw SQL
        sql = """UPDATE core_pharmacymedicine 
                 SET stock_quantity = %s, unit_price = %s, expiry_date = %s
                 WHERE pharmacy_medicine_id = %s"""
        execute_update(sql, (
            form.stock_quantity.data,
            form.unit_price.data,
            form.expiry_date.data,
            stock_id
        ))
        flash(f'Stock for "{stock_item.medicine.name}" updated successfully.', 'success')
        return redirect(url_for('admin.pharmacy_stock'))
    else:
        # Populate form with existing data
        form.stock_quantity.data = stock_item_data['stock_quantity']
        form.unit_price.data = float(stock_item_data['unit_price'])
        form.expiry_date.data = stock_item_data['expiry_date']
    
    return render_template('admin/stock_form.html', form=form, stock_item=stock_item)

