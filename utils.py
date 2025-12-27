"""
Utility functions for business logic validation using raw SQL queries
"""
from datetime import date
from db_utils import fetch_one, execute_update


class ValidationError(Exception):
    """Custom validation error for Flask"""
    pass


def validate_stock_availability(pharmacy, medicine, requested_quantity):
    """
    Validate if sufficient stock is available for a medicine purchase.
    
    Args:
        pharmacy: Pharmacy object or dict with pharmacy_id
        medicine: Medicine object or dict with medicine_id
        requested_quantity: int - quantity requested
    
    Returns:
        tuple: (is_available: bool, available_quantity: int, pharmacy_medicine: dict or None)
    """
    # Get IDs from object or dict
    pharmacy_id = pharmacy.pharmacy_id if hasattr(pharmacy, 'pharmacy_id') else pharmacy.get('pharmacy_id')
    medicine_id = medicine.medicine_id if hasattr(medicine, 'medicine_id') else medicine.get('medicine_id')
    
    # Query using raw SQL
    pharmacy_medicine_data = fetch_one(
        """SELECT * FROM core_pharmacymedicine 
           WHERE pharmacy_id = %s AND medicine_id = %s""",
        (pharmacy_id, medicine_id)
    )
    
    if not pharmacy_medicine_data:
        return False, 0, None
    
    stock_quantity = pharmacy_medicine_data['stock_quantity']
    
    if stock_quantity >= requested_quantity:
        return True, stock_quantity, pharmacy_medicine_data
    else:
        return False, stock_quantity, pharmacy_medicine_data


def reduce_stock(pharmacy, medicine, quantity):
    """
    Reduce stock quantity for a medicine at a pharmacy.
    
    Args:
        pharmacy: Pharmacy object or dict with pharmacy_id
        medicine: Medicine object or dict with medicine_id
        quantity: int - quantity to reduce
    
    Returns:
        dict: Updated pharmacy medicine data
        
    Raises:
        ValidationError: If insufficient stock
    """
    is_available, available_qty, pharmacy_medicine = validate_stock_availability(pharmacy, medicine, quantity)
    
    if not is_available:
        medicine_name = medicine.name if hasattr(medicine, 'name') else medicine.get('name', 'Unknown')
        raise ValidationError(
            f"Insufficient stock for {medicine_name}. "
            f"Requested: {quantity}, Available: {available_qty}"
        )
    
    # Get IDs
    pharmacy_id = pharmacy.pharmacy_id if hasattr(pharmacy, 'pharmacy_id') else pharmacy.get('pharmacy_id')
    medicine_id = medicine.medicine_id if hasattr(medicine, 'medicine_id') else medicine.get('medicine_id')
    
    # Update stock using raw SQL
    new_quantity = pharmacy_medicine['stock_quantity'] - quantity
    sql = """UPDATE core_pharmacymedicine 
             SET stock_quantity = %s 
             WHERE pharmacy_id = %s AND medicine_id = %s"""
    execute_update(sql, (new_quantity, pharmacy_id, medicine_id))
    
    # Return updated data
    pharmacy_medicine['stock_quantity'] = new_quantity
    return pharmacy_medicine


def validate_prescription_expiry(prescription):
    """
    Check if a prescription has expired.
    
    Args:
        prescription: Prescription object or dict with valid_until
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    # Get valid_until from object or dict
    if hasattr(prescription, 'valid_until'):
        valid_until = prescription.valid_until
    elif isinstance(prescription, dict):
        valid_until = prescription.get('valid_until')
    else:
        # If it's an ID, fetch from database
        prescription_id = prescription.prescription_id if hasattr(prescription, 'prescription_id') else prescription
        prescription_data = fetch_one(
            "SELECT valid_until FROM core_prescription WHERE prescription_id = %s",
            (prescription_id,)
        )
        if not prescription_data:
            return False, "Prescription not found"
        valid_until = prescription_data['valid_until']
    
    # Check expiry
    today = date.today()
    if today > valid_until:
        return False, f"Prescription has expired on {valid_until}"
    
    return True, "Prescription is valid"

