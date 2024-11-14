from datetime import datetime, timedelta
from random import choice, randint
from faker import Faker
from app import db, create_app  # Import the app factory function
from app.models import Show  # Import your model

# Initialize Faker
fake = Faker()

# Create the app and push the context
app = create_app()  # Make sure create_app is your factory function in app/__init__.py
with app.app_context():
    # Function to generate random data
    def create_random_entries(num_entries=50):
        entries = []
        for _ in range(num_entries):
            # Generate random names
            first_name = fake.first_name()
            last_name = fake.last_name()

            # Generate random start and end dates within the next year
            start_date = fake.date_between(start_date="today", end_date="+1y")
            end_date = fake.date_between(start_date=start_date, end_date="+1y")

            # Generate random start and end times
            start_time = fake.time_object()
            end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=randint(1, 5))).time()

            # Randomly select days of the week
            days_of_week = ', '.join(fake.random_elements(elements=("mon", "tue", "wed", "thu", "fri", "sat", "sun"), length=randint(1, 7), unique=True))

            # Create a new instance of your model
            entry = Show(
                host_first_name=first_name,
                host_last_name=last_name,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                days_of_week=days_of_week
            )
            entries.append(entry)
        
        # Add entries to the database
        db.session.bulk_save_objects(entries)
        db.session.commit()

    # Call the function to create entries
    create_random_entries()
