import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from core_app.models import BankBranch


class Command(BaseCommand):
    help = "Loads geocoded bank branches from rbi_geocoded_fast.csv into the database"

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, "data_store", "rbi_geocoded_fast.csv")

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found at: {csv_path}"))
            self.stdout.write("Place 'rbi_geocoded_fast.csv' inside backend/data_store/ first.")
            return

        self.stdout.write("Reading CSV dataset...")
        df = pd.read_csv(csv_path, low_memory=False)

        # Retain only records with an identifiable PIN code
        df = df[df["rbi_pincode"].notna()].copy()

        def clean_pin(val):
            try:
                return str(int(float(val)))
            except (ValueError, TypeError):
                return str(val).strip()

        df["clean_pin"] = df["rbi_pincode"].apply(clean_pin)

        # Drop duplicate serial numbers if present to ensure clean batch insert
        if "rbi_serial_number" in df.columns:
            df = df.drop_duplicates(subset=["rbi_serial_number"])

        total_rows = len(df)
        self.stdout.write(f"Preparing {total_rows:,} bank records...")

        # Clear existing bank records to avoid primary key/unique collisions during testing
        BankBranch.objects.all().delete()

        batch_size = 5000
        records = []

        for idx, row in df.iterrows():
            lat = float(row["latitude"]) if pd.notnull(row.get("latitude")) else None
            lon = float(row["longitude"]) if pd.notnull(row.get("longitude")) else None
            serial = float(row["rbi_serial_number"]) if pd.notnull(row.get("rbi_serial_number")) else None

            records.append(
                BankBranch(
                    rbi_serial_number=serial,
                    bank_name=str(row.get("rbi_bank", "")).strip(),
                    branch_name=str(row.get("rbi_branch", "")).strip(),
                    address=str(row.get("rbi_address", "")).strip(),
                    pincode=row["clean_pin"],
                    latitude=lat,
                    longitude=lon,
                )
            )

            if len(records) >= batch_size:
                BankBranch.objects.bulk_create(records)
                self.stdout.write(f"Inserted through row index {idx}...")
                records = []

        if records:
            BankBranch.objects.bulk_create(records)

        count = BankBranch.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Finished. Total BankBranch records in database: {count:,}"))