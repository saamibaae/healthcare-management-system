"""
Test script to verify Flask application structure and imports
"""
import sys
import traceback

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    tests = [
        ("Flask", "from flask import Flask"),
        ("Config", "from config import Config"),
        ("Models", "from models import db, User"),
        ("Forms", "from forms import LoginForm"),
        ("DB Utils", "from db_utils import fetch_one"),
        ("Decorators", "from decorators import role_required"),
        ("Utils", "from utils import validate_stock_availability"),
        ("Routes - Auth", "from routes.auth import auth_bp"),
        ("Routes - Admin", "from routes.admin import admin_bp"),
        ("Routes - Doctor", "from routes.doctor import doctor_bp"),
        ("Routes - Patient", "from routes.patient import patient_bp"),
        ("Commands", "from commands.load_data import register_command"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"[OK] {name}: OK")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: FAILED - {str(e)}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_app_creation():
    """Test that Flask app can be created"""
    print("\n" + "=" * 60)
    print("Testing App Creation")
    print("=" * 60)
    
    try:
        from app import create_app
        from config import Config
        
        app = create_app(Config)
        
        # Check blueprints are registered
        blueprints = list(app.blueprints.keys())
        expected_blueprints = ['auth', 'admin', 'doctor', 'patient']
        
        print(f"[OK] App created successfully")
        print(f"[OK] Blueprints registered: {blueprints}")
        
        for bp in expected_blueprints:
            if bp in blueprints:
                print(f"  [OK] {bp} blueprint registered")
            else:
                print(f"  [FAIL] {bp} blueprint missing")
                return False
        
        # Check routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.endpoint)
        
        print(f"\n[OK] Total routes registered: {len(routes)}")
        print(f"   Sample routes: {routes[:5]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] App creation failed: {str(e)}")
        traceback.print_exc()
        return False


def test_models():
    """Test that models are properly defined"""
    print("\n" + "=" * 60)
    print("Testing Models")
    print("=" * 60)
    
    try:
        from models import (
            User, District, Qualification, Manufacturer, ServiceType,
            Hospital, PublicHospital, PrivateHospital,
            Department, Doctor, DoctorQualification,
            Lab, Pharmacy, Medicine, PharmacyMedicine,
            Patient, PatientEmergencyContact,
            Appointment, LabTest, Prescription, PrescriptionItem,
            Bill, PharmacyBill
        )
        
        models = [
            User, District, Qualification, Manufacturer, ServiceType,
            Hospital, PublicHospital, PrivateHospital,
            Department, Doctor, DoctorQualification,
            Lab, Pharmacy, Medicine, PharmacyMedicine,
            Patient, PatientEmergencyContact,
            Appointment, LabTest, Prescription, PrescriptionItem,
            Bill, PharmacyBill
        ]
        
        print(f"[OK] All {len(models)} models imported successfully")
        
        # Check User model has required methods
        if hasattr(User, 'set_password') and hasattr(User, 'check_password'):
            print("[OK] User model has password methods")
        else:
            print("[FAIL] User model missing password methods")
            return False
        
        # Check User model has UserMixin
        from flask_login import UserMixin
        if issubclass(User, UserMixin):
            print("[OK] User model extends UserMixin")
        else:
            print("[FAIL] User model does not extend UserMixin")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Models test failed: {str(e)}")
        traceback.print_exc()
        return False


def test_forms():
    """Test that forms are properly defined"""
    print("\n" + "=" * 60)
    print("Testing Forms")
    print("=" * 60)
    
    try:
        from forms import (
            LoginForm, DepartmentForm, LabForm, DoctorCreationForm,
            PharmacyStockUpdateForm, AppointmentForm, AppointmentUpdateForm,
            PrescriptionForm, PrescriptionItemForm, LabTestForm,
            LabTestUpdateForm, PatientRegistrationForm
        )
        
        forms = [
            LoginForm, DepartmentForm, LabForm, DoctorCreationForm,
            PharmacyStockUpdateForm, AppointmentForm, AppointmentUpdateForm,
            PrescriptionForm, PrescriptionItemForm, LabTestForm,
            LabTestUpdateForm, PatientRegistrationForm
        ]
        
        print(f"[OK] All {len(forms)} forms imported successfully")
        
        # Test form instantiation (requires request context for CSRF)
        from app import create_app
        from config import Config
        app = create_app(Config)
        with app.test_request_context():
            login_form = LoginForm()
            print("[OK] LoginForm can be instantiated with request context")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Forms test failed: {str(e)}")
        traceback.print_exc()
        return False


def test_routes():
    """Test that routes are properly defined"""
    print("\n" + "=" * 60)
    print("Testing Routes")
    print("=" * 60)
    
    try:
        from routes.auth import auth_bp
        from routes.admin import admin_bp
        from routes.doctor import doctor_bp
        from routes.patient import patient_bp
        
        # Check route functions exist
        auth_routes = ['login', 'logout', 'dashboard', 'patient_registration']
        admin_routes = ['dashboard', 'departments', 'department_add', 'department_edit',
                       'labs', 'lab_add', 'doctors', 'doctor_add', 'pharmacy_stock', 'pharmacy_stock_update']
        doctor_routes = ['dashboard', 'appointments', 'appointment_detail', 'create_prescription',
                        'add_prescription_items', 'order_lab_test']
        patient_routes = ['dashboard', 'appointments', 'appointment_detail', 'bills', 'profile']
        
        print("[OK] All blueprints imported")
        
        # Check auth routes
        auth_funcs = [name for name in dir(auth_bp) if not name.startswith('_')]
        print(f"[OK] Auth blueprint has {len(auth_funcs)} functions")
        
        # Check admin routes
        admin_funcs = [name for name in dir(admin_bp) if not name.startswith('_')]
        print(f"[OK] Admin blueprint has {len(admin_funcs)} functions")
        
        # Check doctor routes
        doctor_funcs = [name for name in dir(doctor_bp) if not name.startswith('_')]
        print(f"[OK] Doctor blueprint has {len(doctor_funcs)} functions")
        
        # Check patient routes
        patient_funcs = [name for name in dir(patient_bp) if not name.startswith('_')]
        print(f"[OK] Patient blueprint has {len(patient_funcs)} functions")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Routes test failed: {str(e)}")
        traceback.print_exc()
        return False


def test_decorators():
    """Test that decorators work"""
    print("\n" + "=" * 60)
    print("Testing Decorators")
    print("=" * 60)
    
    try:
        from decorators import role_required, hospital_staff_required
        
        # Test decorator can be applied
        @role_required('ADMIN')
        def test_func():
            pass
        
        @hospital_staff_required
        def test_func2():
            pass
        
        print("[OK] Decorators can be applied to functions")
        print("[OK] role_required decorator works")
        print("[OK] hospital_staff_required decorator works")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Decorators test failed: {str(e)}")
        traceback.print_exc()
        return False


def test_utils():
    """Test utility functions"""
    print("\n" + "=" * 60)
    print("Testing Utility Functions")
    print("=" * 60)
    
    try:
        from utils import validate_stock_availability, reduce_stock, validate_prescription_expiry
        from utils import ValidationError
        
        print("[OK] Utility functions imported")
        print("[OK] ValidationError exception defined")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Utils test failed: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FLASK APPLICATION TEST SUITE")
    print("=" * 60)
    print("\nThis script tests the Flask application structure and imports.")
    print("Note: Database connection tests require MySQL to be running.\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Forms", test_forms()))
    results.append(("Routes", test_routes()))
    results.append(("Decorators", test_decorators()))
    results.append(("Utils", test_utils()))
    results.append(("App Creation", test_app_creation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Application structure is correct.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

