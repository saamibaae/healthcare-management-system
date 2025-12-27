"""
Flask CLI command to load initial data
Usage: flask load-data
"""
import click
from flask.cli import with_appcontext
from db_utils import get_or_create, execute_insert, fetch_one
from datetime import date


@click.command('load-data')
@with_appcontext
def load_data():
    """Load initial data for hospitals, districts, and other reference tables using raw SQL"""
    click.echo(click.style('Loading initial data...', fg='green'))

    # Create Districts
    click.echo('Creating districts...')
    districts_data = [
        {'name': 'Dhaka', 'division': 'Dhaka'},
        {'name': 'Chittagong', 'division': 'Chittagong'},
        {'name': 'Sylhet', 'division': 'Sylhet'},
        {'name': 'Rajshahi', 'division': 'Rajshahi'},
        {'name': 'Khulna', 'division': 'Khulna'},
    ]
    
    districts = {}
    for district_data in districts_data:
        district, created = get_or_create(
            'core_district',
            {'name': district_data['name']},
            district_data
        )
        districts[district_data['name']] = district
        if created:
            click.echo(f'  Created district: {district["name"]}')

    # Create Service Types
    click.echo('Creating service types...')
    service_types_data = [
        {'name': 'Consultation', 'description': 'Doctor consultation fee'},
        {'name': 'Laboratory', 'description': 'Lab test services'},
        {'name': 'Pharmacy', 'description': 'Medicine purchase'},
        {'name': 'Emergency', 'description': 'Emergency services'},
        {'name': 'Surgery', 'description': 'Surgical procedures'},
    ]
    
    for service_data in service_types_data:
        service, created = get_or_create(
            'core_servicetype',
            {'name': service_data['name']},
            service_data
        )
        if created:
            click.echo(f'  Created service type: {service["name"]}')

    # Create Public Hospitals
    click.echo('Creating public hospitals...')
    public_hospitals_data = [
        {
            'name': 'Dhaka Medical College Hospital',
            'address': 'Bakshibazar, Dhaka-1000',
            'phone': '02-55165088',
            'capacity': 2300,
            'registration_no': 'PUB-DMCH-001',
            'email': 'info@dmch.gov.bd',
            'emergency_services': 1,
            'established_date': date(1946, 7, 10),
            'website': 'http://www.dmch.gov.bd',
            'district_id': districts['Dhaka']['district_id'],
            'govt_funding': 500000000.00,
            'accreditation_level': 'A+',
            'subsidies': 100000000.00,
        },
        {
            'name': 'Kurmitola General Hospital',
            'address': 'Kurmitola, Dhaka-1229',
            'phone': '02-8462321',
            'capacity': 500,
            'registration_no': 'PUB-KGH-002',
            'email': 'info@kgh.gov.bd',
            'emergency_services': 1,
            'established_date': date(1982, 1, 1),
            'website': 'http://www.kgh.gov.bd',
            'district_id': districts['Dhaka']['district_id'],
            'govt_funding': 200000000.00,
            'accreditation_level': 'A',
            'subsidies': 50000000.00,
        },
        {
            'name': 'BSMMU (Bangabandhu Sheikh Mujib Medical University)',
            'address': 'Shahbag, Dhaka-1000',
            'phone': '02-9668477',
            'capacity': 1700,
            'registration_no': 'PUB-BSMMU-003',
            'email': 'info@bsmmu.edu.bd',
            'emergency_services': 1,
            'established_date': date(1998, 4, 30),
            'website': 'http://www.bsmmu.edu.bd',
            'district_id': districts['Dhaka']['district_id'],
            'govt_funding': 800000000.00,
            'accreditation_level': 'A+',
            'subsidies': 150000000.00,
        },
        {
            'name': 'Chittagong Medical College Hospital',
            'address': 'K.B. Fazlul Kader Road, Chittagong',
            'phone': '031-2523311',
            'capacity': 1000,
            'registration_no': 'PUB-CMCH-004',
            'email': 'info@cmch.gov.bd',
            'emergency_services': 1,
            'established_date': date(1957, 1, 1),
            'website': 'http://www.cmch.gov.bd',
            'district_id': districts['Chittagong']['district_id'],
            'govt_funding': 400000000.00,
            'accreditation_level': 'A',
            'subsidies': 80000000.00,
        },
        {
            'name': 'Sylhet MAG Osmani Medical College Hospital',
            'address': 'Medical College Road, Sylhet',
            'phone': '0821-713441',
            'capacity': 750,
            'registration_no': 'PUB-SOMCH-005',
            'email': 'info@somch.gov.bd',
            'emergency_services': 1,
            'established_date': date(1962, 1, 1),
            'website': 'http://www.somch.gov.bd',
            'district_id': districts['Sylhet']['district_id'],
            'govt_funding': 300000000.00,
            'accreditation_level': 'A',
            'subsidies': 60000000.00,
        },
    ]
    
    for hospital_data in public_hospitals_data:
        existing = fetch_one(
            "SELECT hospital_id FROM core_hospital WHERE registration_no = %s",
            (hospital_data['registration_no'],)
        )
        
        if not existing:
            hospital_base_sql = """INSERT INTO core_hospital 
                (name, address, phone, capacity, registration_no, email, emergency_services, 
                 established_date, website, district_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            hospital_id = execute_insert(hospital_base_sql, (
                hospital_data['name'],
                hospital_data['address'],
                hospital_data['phone'],
                hospital_data['capacity'],
                hospital_data['registration_no'],
                hospital_data['email'],
                hospital_data['emergency_services'],
                hospital_data['established_date'],
                hospital_data['website'],
                hospital_data['district_id']
            ))
            
            public_sql = """INSERT INTO core_publichospital 
                (hospital_id, govt_funding, accreditation_level, subsidies)
                VALUES (%s, %s, %s, %s)"""
            execute_insert(public_sql, (
                hospital_id,
                hospital_data['govt_funding'],
                hospital_data['accreditation_level'],
                hospital_data['subsidies']
            ))
            click.echo(f'  Created public hospital: {hospital_data["name"]}')

    # Create Private Hospitals
    click.echo('Creating private hospitals...')
    private_hospitals_data = [
        {
            'name': 'Square Hospital',
            'address': '18/F, Bir Uttam Qazi Nuruzzaman Sarak, West Panthapath, Dhaka-1205',
            'phone': '02-8159457',
            'capacity': 650,
            'registration_no': 'PVT-SQH-001',
            'email': 'info@squarehospital.com',
            'emergency_services': 1,
            'established_date': date(2006, 9, 1),
            'website': 'http://www.squarehospital.com',
            'district_id': districts['Dhaka']['district_id'],
            'owner_name': 'Square Group',
            'profit_margin': 15.50,
        },
        {
            'name': 'United Hospital',
            'address': 'Plot 15, Road 71, Gulshan, Dhaka-1212',
            'phone': '02-9883558',
            'capacity': 500,
            'registration_no': 'PVT-UH-002',
            'email': 'info@uhlbd.com',
            'emergency_services': 1,
            'established_date': date(2006, 4, 4),
            'website': 'http://www.uhlbd.com',
            'district_id': districts['Dhaka']['district_id'],
            'owner_name': 'United Group',
            'profit_margin': 18.00,
        },
        {
            'name': 'Evercare Hospital Dhaka',
            'address': 'Plot 81, Block E, Bashundhara R/A, Dhaka-1229',
            'phone': '02-55089090',
            'capacity': 450,
            'registration_no': 'PVT-EVH-003',
            'email': 'info@evercarebd.com',
            'emergency_services': 1,
            'established_date': date(2015, 11, 1),
            'website': 'http://www.evercarebd.com',
            'district_id': districts['Dhaka']['district_id'],
            'owner_name': 'Evercare Group',
            'profit_margin': 20.00,
        },
        {
            'name': 'Labaid Specialized Hospital',
            'address': 'House 1, Road 4, Dhanmondi, Dhaka-1205',
            'phone': '02-8616292',
            'capacity': 300,
            'registration_no': 'PVT-LBD-004',
            'email': 'info@labaid.com.bd',
            'emergency_services': 1,
            'established_date': date(2004, 1, 1),
            'website': 'http://www.labaid.com.bd',
            'district_id': districts['Dhaka']['district_id'],
            'owner_name': 'Labaid Group',
            'profit_margin': 16.00,
        },
        {
            'name': 'Ibn Sina Hospital',
            'address': 'House 48, Road 9/A, Dhanmondi, Dhaka-1209',
            'phone': '02-9661991',
            'capacity': 250,
            'registration_no': 'PVT-ISH-005',
            'email': 'info@ibnsinahospital.com',
            'emergency_services': 1,
            'established_date': date(2008, 1, 1),
            'website': 'http://www.ibnsinahospital.com',
            'district_id': districts['Dhaka']['district_id'],
            'owner_name': 'Ibn Sina Trust',
            'profit_margin': 14.50,
        },
    ]
    
    for hospital_data in private_hospitals_data:
        existing = fetch_one(
            "SELECT hospital_id FROM core_hospital WHERE registration_no = %s",
            (hospital_data['registration_no'],)
        )
        
        if not existing:
            hospital_base_sql = """INSERT INTO core_hospital 
                (name, address, phone, capacity, registration_no, email, emergency_services, 
                 established_date, website, district_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            hospital_id = execute_insert(hospital_base_sql, (
                hospital_data['name'],
                hospital_data['address'],
                hospital_data['phone'],
                hospital_data['capacity'],
                hospital_data['registration_no'],
                hospital_data['email'],
                hospital_data['emergency_services'],
                hospital_data['established_date'],
                hospital_data['website'],
                hospital_data['district_id']
            ))
            
            private_sql = """INSERT INTO core_privatehospital 
                (hospital_id, owner_name, profit_margin)
                VALUES (%s, %s, %s)"""
            execute_insert(private_sql, (
                hospital_id,
                hospital_data['owner_name'],
                hospital_data['profit_margin']
            ))
            click.echo(f'  Created private hospital: {hospital_data["name"]}')

    # Create Qualifications
    click.echo('Creating qualifications...')
    qualifications_data = [
        {'code': 'MBBS', 'degree_name': 'Bachelor of Medicine, Bachelor of Surgery'},
        {'code': 'MD', 'degree_name': 'Doctor of Medicine'},
        {'code': 'MS', 'degree_name': 'Master of Surgery'},
        {'code': 'FCPS', 'degree_name': 'Fellow of the College of Physicians and Surgeons'},
        {'code': 'FRCS', 'degree_name': 'Fellow of the Royal College of Surgeons'},
    ]
    
    for qual_data in qualifications_data:
        qual, created = get_or_create(
            'core_qualification',
            {'code': qual_data['code']},
            qual_data
        )
        if created:
            click.echo(f'  Created qualification: {qual["code"]}')

    # Create Manufacturers
    click.echo('Creating manufacturers...')
    manufacturers_data = [
        {
            'name': 'Square Pharmaceuticals Ltd',
            'phone': '02-8159635',
            'address': 'SQUARE Centre, 48 Mohakhali C/A, Dhaka-1212',
            'license_no': 'MFG-SQ-001',
        },
        {
            'name': 'Beximco Pharmaceuticals Ltd',
            'phone': '02-8808176',
            'address': '17 Dhanmondi R/A, Dhaka-1209',
            'license_no': 'MFG-BX-002',
        },
        {
            'name': 'Incepta Pharmaceuticals Ltd',
            'phone': '02-7791447',
            'address': '40 Shahid Tajuddin Ahmed Sarani, Dhaka-1208',
            'license_no': 'MFG-IN-003',
        },
    ]
    
    for mfg_data in manufacturers_data:
        mfg, created = get_or_create(
            'core_manufacturer',
            {'license_no': mfg_data['license_no']},
            mfg_data
        )
        if created:
            click.echo(f'  Created manufacturer: {mfg["name"]}')

    click.echo(click.style('Initial data loaded successfully!', fg='green'))


def register_command(app):
    """Register the command with Flask app"""
    app.cli.add_command(load_data)

