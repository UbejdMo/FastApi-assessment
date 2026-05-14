import random
import sys
from datetime import date,timedelta
from pathlib import Path
from faker import Faker

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import Author,Book,Category,Loan,Member,book_authors

random.seed(42)
fake = Faker()
Faker.seed(42)

def clear_existing_data(db):
    db.query(Loan).delete()
    db.execute(book_authors.delete())
    db.query(Book).delete()
    db.query(Author).delete()
    db.query(Category).delete()
    db.query(Member).delete()
    db.commit()

def seed_categories(db):
    names = ["Fiction","Non-fiction","Science","History","Biography"]
    categories = [Category(name=n)for n in names]
    db.add_all(categories)
    db.commit()
    return categories

def seed_authors(db,n=10):
    countries = [
        "United States","United Kingdom","France","Germany",
        "Japan","Brazil","Albania","Kosovo","Italy","Spain"
    ]
    authors = [
        Author(full_name = fake.name(), country = random.choice(countries))
        for _ in range(n)
    ]
    db.add_all(authors)
    db.commit()
    return authors

def seed_books(db,categories,authors,n=25):
    books =[]
    for _ in range(n):
        book = Book(
            title = fake.sentence(nb_words=random.randint(2,5)).rstrip("."),
            isbn = fake.unique.isbn13(),
            category_id = random.choice(categories).id,
            total_copies = random.randint(1,5),
            published_year = random.randint(1950,2024)
        )
        num_authors = random.choices([1,2,3], weights=[60,30,10])[0]
        book.authors = random.sample(authors,num_authors)
        books.append(book)
    db.add_all(books)
    db.commit()
    return books

def seed_members(db,n=12):
    members = [
        Member(
            full_name = fake.name(),
            email = fake.unique.email(),
            join_date = fake.date_between(start_date="-2y",end_date="today"),
            is_active = random.random()>0.1
        )
        for _ in range(n)
    ]  
    db.add_all(members)
    db.commit()
    return members

def seed_loans(db, members, books):
    loans = []
    for _ in range(12):
        loan_date = fake.date_between(start_date="-1y", end_date="-30d")
        loans.append(Loan(
            member_id=random.choice(members).id,
            book_id=random.choice(books).id,
            loan_date=loan_date,
            due_date=loan_date + timedelta(days=14),
            return_date=loan_date + timedelta(days=random.randint(3, 21)),
        ))

    for _ in range(12):
        loan_date = fake.date_between(start_date="-10d", end_date="today")
        loans.append(Loan(
            member_id=random.choice(members).id,
            book_id=random.choice(books).id,
            loan_date=loan_date,
            due_date=loan_date + timedelta(days=14),
            return_date=None,
        ))

    # 8 overdue loans: due_date in the past, not returned.
    for _ in range(8):
        loan_date = fake.date_between(start_date="-60d", end_date="-21d")
        loans.append(Loan(
            member_id=random.choice(members).id,
            book_id=random.choice(books).id,
            loan_date=loan_date,
            due_date=loan_date + timedelta(days=14),
            return_date=None,
        ))

    db.add_all(loans)
    db.commit()
    return loans

def main():
    db = SessionLocal()
    try:
        print("Clearing existing data...")
        clear_existing_data(db)

        print("Seeding categories...")
        categories = seed_categories(db)
        print(f" -> {len(categories)} categories")

        print("Seeding authors...")
        authors = seed_authors(db)
        print(f" -> {len(authors)} authors")

        print("Seeding books...")
        books = seed_books(db, categories, authors)
        coauthored = sum(1 for b in books if len(b.authors) > 1)
        print(f"  → {len(books)} books ({coauthored} co-authored)")

        print("Seeding members...")
        members = seed_members(db)
        inactive = sum(1 for m in members if not m.is_active)
        print(f"  → {len(members)} members ({inactive} inactive)")

        print("Seeding loans...")
        loans = seed_loans(db, members, books)
        today = date.today()
        returned = sum(1 for l in loans if l.return_date is not None)
        active = sum(1 for l in loans if l.return_date is None and l.due_date >= today)
        overdue = sum(1 for l in loans if l.return_date is None and l.due_date < today)
        print(f"  → {len(loans)} loans ({returned} returned, {active} active, {overdue} overdue)")

        print("\nSeed complete.")
    finally:
        db.close()

if __name__ == "__main__":
    main()