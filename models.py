"""
SQLAlchemy models mapped to existing MySQL tables
All table names match Django's naming convention (core_*)
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# ==================== User Model ====================
class User(UserMixin, db.Model):
    """Custom User model with role-based access"""
    __tablename__ = 'core_customuser'
    
    id = Column(Integer, primary_key=True, name='id')
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(128), nullable=False)  # Will store hashed password
    email = Column(String(254), nullable=True)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Custom fields
    role = Column(String(10), nullable=False)  # ADMIN, DOCTOR, PATIENT
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), nullable=True)
    
    # Relationships
    hospital = relationship('Hospital', foreign_keys=[hospital_id], backref='users')
    doctor_profile = relationship('Doctor', backref='user', uselist=False)
    patient_profile = relationship('Patient', backref='user', uselist=False)
    
    ROLE_CHOICES = [
        ('ADMIN', 'Hospital Admin'),
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
    ]
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)
    
    def get_role_display(self):
        """Get human-readable role name"""
        role_dict = dict(self.ROLE_CHOICES)
        return role_dict.get(self.role, self.role)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ==================== Reference Tables ====================
class District(db.Model):
    __tablename__ = 'core_district'
    
    district_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    division = Column(String(100), nullable=False)
    
    hospitals = relationship('Hospital', backref='district')
    
    def __repr__(self):
        return f"<District {self.name}, {self.division}>"


class Qualification(db.Model):
    __tablename__ = 'core_qualification'
    
    qualification_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    degree_name = Column(String(200), nullable=False)
    
    doctor_qualifications = relationship('DoctorQualification', backref='qualification')
    
    def __repr__(self):
        return f"<Qualification {self.code} - {self.degree_name}>"


class Manufacturer(db.Model):
    __tablename__ = 'core_manufacturer'
    
    manufacturer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(Text, nullable=False)
    license_no = Column(String(100), unique=True, nullable=False)
    
    medicines = relationship('Medicine', backref='manufacturer')
    
    def __repr__(self):
        return f"<Manufacturer {self.name}>"


class ServiceType(db.Model):
    __tablename__ = 'core_servicetype'
    
    service_type_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    bills = relationship('Bill', backref='service_type')
    
    def __repr__(self):
        return f"<ServiceType {self.name}>"


# ==================== Hospital Models (Inheritance) ====================
class Hospital(db.Model):
    """Base Hospital model"""
    __tablename__ = 'core_hospital'
    
    hospital_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(15), nullable=False)
    capacity = Column(Integer, nullable=False)
    registration_no = Column(String(100), unique=True, nullable=False)
    email = Column(String(254), nullable=False)
    emergency_services = Column(Boolean, default=True)
    established_date = Column(Date, nullable=False)
    website = Column(String(200), nullable=True)
    district_id = Column(Integer, ForeignKey('core_district.district_id'), nullable=False)
    
    # Relationships
    departments = relationship('Department', backref='hospital', cascade='all, delete-orphan')
    doctors = relationship('Doctor', backref='hospital', cascade='all, delete-orphan')
    labs = relationship('Lab', backref='hospital', cascade='all, delete-orphan')
    pharmacies = relationship('Pharmacy', backref='hospital', cascade='all, delete-orphan')
    
    # Polymorphic discriminator
    hospital_type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'hospital',
        'polymorphic_on': hospital_type
    }
    
    def __repr__(self):
        return f"<Hospital {self.name}>"


class PublicHospital(Hospital):
    """Public Hospital - inherits from Hospital"""
    __tablename__ = 'core_publichospital'
    
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), primary_key=True)
    govt_funding = Column(Numeric(15, 2), nullable=False)
    accreditation_level = Column(String(50), nullable=False)
    subsidies = Column(Numeric(15, 2), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'public'
    }
    
    def __repr__(self):
        return f"<PublicHospital {self.name}>"


class PrivateHospital(Hospital):
    """Private Hospital - inherits from Hospital"""
    __tablename__ = 'core_privatehospital'
    
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), primary_key=True)
    owner_name = Column(String(200), nullable=False)
    profit_margin = Column(Numeric(5, 2), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'private'
    }
    
    def __repr__(self):
        return f"<PrivateHospital {self.name}>"


# ==================== Department ====================
class Department(db.Model):
    __tablename__ = 'core_department'
    
    dept_id = Column(Integer, primary_key=True, autoincrement=True)
    dept_name = Column(String(100), nullable=False)
    floor = Column(String(20), nullable=False)
    head_doctor_id = Column(Integer, nullable=True)
    extension = Column(String(20), nullable=True)
    operating_hours = Column(String(100), nullable=False)
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), nullable=False)
    
    doctors = relationship('Doctor', backref='dept')
    
    __table_args__ = (
        UniqueConstraint('dept_name', 'hospital_id', name='core_department_dept_name_hospital_id_key'),
    )
    
    def __repr__(self):
        return f"<Department {self.dept_name} - {self.hospital.name}>"


# ==================== Doctor ====================
class Doctor(db.Model):
    __tablename__ = 'core_doctor'
    
    GENDER_CHOICES = ['M', 'F', 'O']
    
    doctor_id = Column(Integer, primary_key=True, autoincrement=True)
    license_no = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    specialization = Column(String(200), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(254), nullable=False)
    experience_yrs = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)  # M, F, O
    shift_timing = Column(String(100), nullable=False)
    join_date = Column(Date, nullable=False)
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), nullable=False)
    dept_id = Column(Integer, ForeignKey('core_department.dept_id'), nullable=True)
    user_id = Column(Integer, ForeignKey('core_customuser.id'), nullable=True)
    
    appointments = relationship('Appointment', backref='doctor')
    ordered_tests = relationship('LabTest', backref='ordered_by')
    qualifications = relationship('DoctorQualification', backref='doctor', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Doctor Dr. {self.full_name} - {self.specialization}>"


# ==================== Doctor Qualification ====================
class DoctorQualification(db.Model):
    __tablename__ = 'core_doctorqualification'
    
    doctor_qualification_id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey('core_doctor.doctor_id'), nullable=False)
    qualification_id = Column(Integer, ForeignKey('core_qualification.qualification_id'), nullable=False)
    year_obtained = Column(Integer, nullable=False)
    institution_name = Column(String(200), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('doctor_id', 'qualification_id', name='core_doctorqualification_doctor_id_qualification_id_key'),
    )
    
    def __repr__(self):
        return f"<DoctorQualification {self.doctor.full_name} - {self.qualification.code}>"


# ==================== Lab ====================
class Lab(db.Model):
    __tablename__ = 'core_lab'
    
    lab_id = Column(Integer, primary_key=True, autoincrement=True)
    lab_name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    phone = Column(String(15), nullable=False)
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), nullable=False)
    
    tests = relationship('LabTest', backref='lab')
    
    def __repr__(self):
        return f"<Lab {self.lab_name} - {self.hospital.name}>"


# ==================== Pharmacy ====================
class Pharmacy(db.Model):
    __tablename__ = 'core_pharmacy'
    
    pharmacy_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    employee_count = Column(Integer, nullable=False)
    hospital_id = Column(Integer, ForeignKey('core_hospital.hospital_id'), nullable=False)
    
    medicines = relationship('PharmacyMedicine', backref='pharmacy', cascade='all, delete-orphan')
    bills = relationship('PharmacyBill', backref='pharmacy')
    
    def __repr__(self):
        return f"<Pharmacy {self.name} - {self.hospital.name}>"


# ==================== Medicine ====================
class Medicine(db.Model):
    __tablename__ = 'core_medicine'
    
    medicine_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)
    dosage_info = Column(Text, nullable=False)
    side_effects = Column(Text, nullable=True)
    manufacturer_id = Column(Integer, ForeignKey('core_manufacturer.manufacturer_id'), nullable=False)
    
    pharmacy_stock = relationship('PharmacyMedicine', backref='medicine')
    prescription_items = relationship('PrescriptionItem', backref='medicine')
    
    def __repr__(self):
        return f"<Medicine {self.name} ({self.type})>"


# ==================== Pharmacy Medicine ====================
class PharmacyMedicine(db.Model):
    __tablename__ = 'core_pharmacymedicine'
    
    pharmacy_medicine_id = Column(Integer, primary_key=True, autoincrement=True)
    pharmacy_id = Column(Integer, ForeignKey('core_pharmacy.pharmacy_id'), nullable=False)
    medicine_id = Column(Integer, ForeignKey('core_medicine.medicine_id'), nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    expiry_date = Column(Date, nullable=False)
    batch_number = Column(String(100), nullable=False)
    last_restocked = Column(Date, default=date.today)
    
    __table_args__ = (
        UniqueConstraint('pharmacy_id', 'medicine_id', 'batch_number', name='core_pharmacymedicine_pharmacy_id_medicine_id_batch_number_key'),
    )
    
    def __repr__(self):
        return f"<PharmacyMedicine {self.medicine.name} @ {self.pharmacy.name} (Stock: {self.stock_quantity})>"


# ==================== Patient ====================
class Patient(db.Model):
    __tablename__ = 'core_patient'
    
    GENDER_CHOICES = ['M', 'F', 'O']
    BLOOD_TYPE_CHOICES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    MARITAL_STATUS_CHOICES = ['Single', 'Married', 'Divorced', 'Widowed']
    
    patient_id = Column(Integer, primary_key=True, autoincrement=True)
    national_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(254), nullable=False)
    address = Column(Text, nullable=False)
    blood_type = Column(String(3), nullable=False)
    occupation = Column(String(100), nullable=True)
    date_of_death = Column(Date, nullable=True)
    marital_status = Column(String(20), nullable=False)
    birth_place = Column(String(200), nullable=False)
    father_name = Column(String(200), nullable=False)
    mother_name = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey('core_customuser.id'), nullable=True)
    
    appointments = relationship('Appointment', backref='patient')
    lab_tests = relationship('LabTest', backref='patient')
    bills = relationship('Bill', backref='patient')
    emergency_contacts = relationship('PatientEmergencyContact', backref='patient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Patient {self.full_name} (ID: {self.national_id})>"


# ==================== Patient Emergency Contact ====================
class PatientEmergencyContact(db.Model):
    __tablename__ = 'core_patientemergencycontact'
    
    contact_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('core_patient.patient_id'), nullable=False)
    contact_name = Column(String(200), nullable=False)
    contact_phone = Column(String(15), nullable=False)
    relationship = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<PatientEmergencyContact {self.contact_name} ({self.patient.full_name})>"


# ==================== Appointment ====================
class Appointment(db.Model):
    __tablename__ = 'core_appointment'
    
    STATUS_CHOICES = ['Scheduled', 'Completed', 'Cancelled', 'No-Show']
    VISIT_TYPE_CHOICES = ['First Visit', 'Follow-up', 'Emergency']
    
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('core_patient.patient_id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('core_doctor.doctor_id'), nullable=False)
    status = Column(String(20), default='Scheduled', nullable=False)
    reason_for_visit = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    symptoms = Column(Text, nullable=False)
    visit_type = Column(String(20), nullable=False)
    date_and_time = Column(DateTime, nullable=False)
    
    prescriptions = relationship('Prescription', backref='appointment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Appointment {self.patient.full_name} with Dr. {self.doctor.full_name} on {self.date_and_time}>"


# ==================== Lab Test ====================
class LabTest(db.Model):
    __tablename__ = 'core_labtest'
    
    STATUS_CHOICES = ['Ordered', 'In Progress', 'Completed']
    
    test_id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey('core_lab.lab_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('core_patient.patient_id'), nullable=False)
    test_type = Column(String(200), nullable=False)
    result = Column(Text, nullable=True)
    ordered_by_id = Column(Integer, ForeignKey('core_doctor.doctor_id'), nullable=False)
    remarks = Column(Text, nullable=True)
    test_cost = Column(Numeric(10, 2), nullable=False)
    date_and_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='Ordered', nullable=False)
    
    def __repr__(self):
        return f"<LabTest {self.test_type} for {self.patient.full_name}>"


# ==================== Prescription ====================
class Prescription(db.Model):
    __tablename__ = 'core_prescription'
    
    prescription_id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey('core_appointment.appointment_id'), nullable=False)
    valid_until = Column(Date, nullable=False)
    refill_count = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    
    items = relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan')
    pharmacy_bills = relationship('PharmacyBill', backref='prescription')
    
    @property
    def is_expired(self):
        """Check if prescription has expired"""
        from datetime import date
        return date.today() > self.valid_until
    
    def __repr__(self):
        return f"<Prescription #{self.prescription_id} for {self.appointment.patient.full_name}>"


# ==================== Prescription Item ====================
class PrescriptionItem(db.Model):
    __tablename__ = 'core_prescriptionitem'
    
    BEFORE_AFTER_CHOICES = ['Before', 'After', 'With']
    
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, ForeignKey('core_prescription.prescription_id'), nullable=False)
    medicine_id = Column(Integer, ForeignKey('core_medicine.medicine_id'), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    before_after_meal = Column(String(20), nullable=False)
    instructions = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PrescriptionItem {self.medicine.name} - {self.dosage}>"


# ==================== Bill ====================
class Bill(db.Model):
    __tablename__ = 'core_bill'
    
    STATUS_CHOICES = ['Pending', 'Paid', 'Partial', 'Cancelled']
    
    bill_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('core_patient.patient_id'), nullable=False)
    service_type_id = Column(Integer, ForeignKey('core_servicetype.service_type_id'), nullable=False)
    bill_date = Column(Date, default=date.today)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default='Pending', nullable=False)
    insurance_covered = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    discount = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    tax = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    due_date = Column(Date, nullable=False)
    transaction_id = Column(String(100), nullable=True)
    
    pharmacy_bill = relationship('PharmacyBill', backref='bill', uselist=False)
    
    def __repr__(self):
        return f"<Bill #{self.bill_id} - {self.patient.full_name} - BDT {self.total_amount}>"


# ==================== Pharmacy Bill ====================
class PharmacyBill(db.Model):
    __tablename__ = 'core_pharmacybill'
    
    pharmacy_bill_id = Column(Integer, primary_key=True, autoincrement=True)
    pharmacy_id = Column(Integer, ForeignKey('core_pharmacy.pharmacy_id'), nullable=False)
    bill_id = Column(Integer, ForeignKey('core_bill.bill_id'), unique=True, nullable=False)
    purchase_date = Column(Date, default=date.today)
    prescription_id = Column(Integer, ForeignKey('core_prescription.prescription_id'), nullable=True)
    
    def __repr__(self):
        return f"<PharmacyBill #{self.pharmacy_bill_id} - {self.pharmacy.name}>"

