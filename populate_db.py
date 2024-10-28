from faker import Faker
from models import db, Show
from app import app
from datetime import datetime, timedelta
import random

fake = Faker()
NUM_ENTRIES = 200
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

with app.app_context():
    for _ in range(NUM_ENTRIES):

        host_first_name = fake.first_name()
        host_last_name = fake.last_name()

        start_date = datetime.today() + timedelta(days=random.randint(0, 30))
        end_date = start_date + timedelta(days=random.randint(1, 14))
       
        start_time = fake.time_object()
        end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=random.randint(30, 120))).time()

        days_of_week = random.choice(DAYS_OF_WEEK)
        
        show = Show(
            host_first_name=host_first_name,
            host_last_name=host_last_name,
            start_date=start_date.date(),
            end_date=end_date.date(),
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week
        )
        db.session.add(show)
    db.session.commit()
    print(f"{NUM_ENTRIES} shows added to the database.")
