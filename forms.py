"""
WTForms definitions for Flask application
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, DecimalField, DateField, DateTimeField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError
from datetime import date, datetime


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(max=150)], 
                          render_kw={'class': 'form-control', 'placeholder': 'Username'})
    password = PasswordField('Password', validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'placeholder': 'Password'})


class DepartmentForm(FlaskForm):
    """Department creation/editing form"""
    dept_name = StringField('Department Name', validators=[DataRequired(), Length(max=100)],
                           render_kw={'class': 'form-control'})
    floor = StringField('Floor', validators=[DataRequired(), Length(max=20)],
                      render_kw={'class': 'form-control'})
    extension = StringField('Extension', validators=[Optional(), Length(max=20)],
                          render_kw={'class': 'form-control'})
    operating_hours = StringField('Operating Hours', validators=[DataRequired(), Length(max=100)],
                                 render_kw={'class': 'form-control', 'placeholder': 'e.g., 8:00 AM - 5:00 PM'})


class LabForm(FlaskForm):
    """Lab creation/editing form"""
    lab_name = StringField('Lab Name', validators=[DataRequired(), Length(max=200)],
                          render_kw={'class': 'form-control'})
    location = StringField('Location', validators=[DataRequired(), Length(max=200)],
                          render_kw={'class': 'form-control'})
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)],
                       render_kw={'class': 'form-control'})


class DoctorCreationForm(FlaskForm):
    """Doctor creation form"""
    username = StringField('Username', validators=[DataRequired(), Length(max=150)],
                          render_kw={'class': 'form-control'})
    password = PasswordField('Password', validators=[DataRequired()],
                            render_kw={'class': 'form-control'})
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')],
                                     render_kw={'class': 'form-control'})
    license_no = StringField('License Number', validators=[DataRequired(), Length(max=100)],
                            render_kw={'class': 'form-control'})
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)],
                           render_kw={'class': 'form-control'})
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=200)],
                               render_kw={'class': 'form-control'})
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)],
                       render_kw={'class': 'form-control'})
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=254)],
                       render_kw={'class': 'form-control'})
    experience_yrs = IntegerField('Experience (Years)', validators=[DataRequired(), NumberRange(min=0)],
                                 render_kw={'class': 'form-control'})
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
                       validators=[DataRequired()], render_kw={'class': 'form-control'})
    shift_timing = StringField('Shift Timing', validators=[DataRequired(), Length(max=100)],
                              render_kw={'class': 'form-control', 'placeholder': 'e.g., 9 AM - 5 PM'})
    join_date = DateField('Join Date', validators=[DataRequired()],
                         render_kw={'class': 'form-control', 'type': 'date'})
    dept = SelectField('Department', coerce=int, validators=[Optional()],
                      render_kw={'class': 'form-control'})


class PharmacyStockUpdateForm(FlaskForm):
    """Pharmacy stock update form"""
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)],
                                 render_kw={'class': 'form-control'})
    unit_price = DecimalField('Unit Price', validators=[DataRequired(), NumberRange(min=0)],
                            places=2, render_kw={'class': 'form-control', 'step': '0.01'})
    expiry_date = DateField('Expiry Date', validators=[DataRequired()],
                           render_kw={'class': 'form-control', 'type': 'date'})


class AppointmentForm(FlaskForm):
    """Appointment creation form"""
    patient = SelectField('Patient', coerce=int, validators=[DataRequired()],
                        render_kw={'class': 'form-control'})
    doctor = SelectField('Doctor', coerce=int, validators=[DataRequired()],
                        render_kw={'class': 'form-control'})
    reason_for_visit = TextAreaField('Reason for Visit', validators=[DataRequired()],
                                     render_kw={'class': 'form-control', 'rows': 3})
    symptoms = TextAreaField('Symptoms', validators=[DataRequired()],
                           render_kw={'class': 'form-control', 'rows': 3})
    visit_type = SelectField('Visit Type', 
                            choices=[('First Visit', 'First Visit'), ('Follow-up', 'Follow-up'), ('Emergency', 'Emergency')],
                            validators=[DataRequired()], render_kw={'class': 'form-control'})
    date_and_time = DateTimeField('Date and Time', validators=[DataRequired()],
                                 format='%Y-%m-%dT%H:%M',
                                 render_kw={'class': 'form-control', 'type': 'datetime-local'})


class AppointmentUpdateForm(FlaskForm):
    """Appointment update form"""
    status = SelectField('Status',
                        choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), 
                                ('Cancelled', 'Cancelled'), ('No-Show', 'No-Show')],
                        validators=[DataRequired()], render_kw={'class': 'form-control'})
    diagnosis = TextAreaField('Diagnosis', validators=[Optional()],
                             render_kw={'class': 'form-control', 'rows': 4})
    follow_up_date = DateField('Follow-up Date', validators=[Optional()],
                              render_kw={'class': 'form-control', 'type': 'date'})


class PrescriptionForm(FlaskForm):
    """Prescription creation form"""
    valid_until = DateField('Valid Until', validators=[DataRequired()],
                           render_kw={'class': 'form-control', 'type': 'date'})
    refill_count = IntegerField('Refill Count', validators=[Optional(), NumberRange(min=0)],
                               render_kw={'class': 'form-control'})
    notes = TextAreaField('Notes', validators=[Optional()],
                         render_kw={'class': 'form-control', 'rows': 3})


class PrescriptionItemForm(FlaskForm):
    """Prescription item form"""
    medicine = SelectField('Medicine', coerce=int, validators=[DataRequired()],
                         render_kw={'class': 'form-control'})
    dosage = StringField('Dosage', validators=[DataRequired(), Length(max=100)],
                       render_kw={'class': 'form-control', 'placeholder': 'e.g., 500mg'})
    frequency = StringField('Frequency', validators=[DataRequired(), Length(max=100)],
                          render_kw={'class': 'form-control', 'placeholder': 'e.g., Twice daily'})
    duration = StringField('Duration', validators=[DataRequired(), Length(max=100)],
                          render_kw={'class': 'form-control', 'placeholder': 'e.g., 7 days'})
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)],
                          render_kw={'class': 'form-control'})
    before_after_meal = SelectField('Before/After Meal',
                                    choices=[('Before', 'Before'), ('After', 'After'), ('With', 'With')],
                                    validators=[DataRequired()], render_kw={'class': 'form-control'})
    instructions = TextAreaField('Instructions', validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 2})


class LabTestForm(FlaskForm):
    """Lab test ordering form"""
    lab = SelectField('Lab', coerce=int, validators=[DataRequired()],
                     render_kw={'class': 'form-control'})
    patient = SelectField('Patient', coerce=int, validators=[DataRequired()],
                         render_kw={'class': 'form-control'})
    test_type = StringField('Test Type', validators=[DataRequired(), Length(max=200)],
                           render_kw={'class': 'form-control', 'placeholder': 'e.g., Complete Blood Count'})
    test_cost = DecimalField('Test Cost', validators=[DataRequired(), NumberRange(min=0)],
                           places=2, render_kw={'class': 'form-control', 'step': '0.01'})
    remarks = TextAreaField('Remarks', validators=[Optional()],
                          render_kw={'class': 'form-control', 'rows': 3})


class LabTestUpdateForm(FlaskForm):
    """Lab test update form"""
    status = SelectField('Status',
                       choices=[('Ordered', 'Ordered'), ('In Progress', 'In Progress'), ('Completed', 'Completed')],
                       validators=[DataRequired()], render_kw={'class': 'form-control'})
    result = TextAreaField('Result', validators=[Optional()],
                          render_kw={'class': 'form-control', 'rows': 4})


class PatientRegistrationForm(FlaskForm):
    """Patient registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(max=150)],
                          render_kw={'class': 'form-control'})
    password = PasswordField('Password', validators=[DataRequired()],
                            render_kw={'class': 'form-control'})
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')],
                                     render_kw={'class': 'form-control'})
    national_id = StringField('National ID', validators=[DataRequired(), Length(max=50)],
                             render_kw={'class': 'form-control'})
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)],
                          render_kw={'class': 'form-control'})
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()],
                             render_kw={'class': 'form-control', 'type': 'date'})
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
                       validators=[DataRequired()], render_kw={'class': 'form-control'})
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)],
                       render_kw={'class': 'form-control'})
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=254)],
                       render_kw={'class': 'form-control'})
    address = TextAreaField('Address', validators=[DataRequired()],
                           render_kw={'class': 'form-control', 'rows': 3})
    blood_type = SelectField('Blood Type',
                           choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                                   ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')],
                           validators=[DataRequired()], render_kw={'class': 'form-control'})
    occupation = StringField('Occupation', validators=[Optional(), Length(max=100)],
                            render_kw={'class': 'form-control'})
    marital_status = SelectField('Marital Status',
                                choices=[('Single', 'Single'), ('Married', 'Married'),
                                       ('Divorced', 'Divorced'), ('Widowed', 'Widowed')],
                                validators=[DataRequired()], render_kw={'class': 'form-control'})
    birth_place = StringField('Birth Place', validators=[DataRequired(), Length(max=200)],
                             render_kw={'class': 'form-control'})
    father_name = StringField('Father Name', validators=[DataRequired(), Length(max=200)],
                             render_kw={'class': 'form-control'})
    mother_name = StringField('Mother Name', validators=[DataRequired(), Length(max=200)],
                             render_kw={'class': 'form-control'})

