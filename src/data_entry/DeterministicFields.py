# Author: Alden Sahi
# Date: 09/10/2026
# Program Name: DeterministicFields.py
# Program Description: Data that can is persistent and deterministic on the field in job posting
from typing import Union, List
import json

determisitic_data:dict[str, Union[str, List[dict[str,str]]]] = {}


print("="*60)
print("="*19 + " Welcome to Oppurtunisitic " + "="*19)
print("="*60 + "\n")

print("Please enter the following information so that we can properly fill out the job posting fields for you.\n")


# INFORMATION
print("\nBASIC INFORMATION:")
determisitic_data["first_name"] = input("First Name: ")
determisitic_data["last_name"] = input("Last Name: ")
determisitic_data["mobile_number"] = input("Mobile Number: ")
determisitic_data["email"] = input("Email Address: ")
determisitic_data["address_line1"] = input("Street Address: ")
determisitic_data["city"] = input("City: ")
determisitic_data["state"] = input("State/Province: ")
determisitic_data["zip_code"] = input("Zip/Postal Code: ")
determisitic_data["country"] = input("Country: ")
determisitic_data["linkedin_url"] = input("LinkedIn Profile URL: ")
determisitic_data["website_url"] = input("Personal Website/Portfolio URL: ")
determisitic_data["desired_salary"] = input("Desired Salary: ")
determisitic_data["work_authorization"] = input("Are you legally authorized to work in this country? (Yes/No): ")
determisitic_data["require_sponsorship"] = input("Will you now or in the future require visa sponsorship? (Yes/No): ")

# EDUCATION HISTORY
print("\nEDUCATION HISTORY:")
determisitic_data["education_history"] = []
more_history:bool = True
while more_history:
    education_entry: dict[str,str] = {}
    education_entry["school_name"] = input("School Name: ")
    education_entry["degree"] = input("Degree: ")
    education_entry["area_of_study"] = input("Area of Study: ")
    education_entry["start_date"] = input("Start Date (MM/YYYY): ")
    education_entry["end_date"] = input("End Date (MM/YYYY or 'Present'): ")
    education_entry["gpa"] = input("GPA (if applicable): ")
    determisitic_data["education_history"].append(education_entry)

    # ANOTHER EDUCATION ENTRY ??
    while True:
        more_history_input:str = input("Do you want to add another education entry? (Yes/No): ")
        cleaned_input:str = more_history_input.strip().lower()
        match cleaned_input:
            case "yes":
                more_history = True
                break
            case "no":
                more_history = False
                break
            case _:
                print("Invalid input. Please enter 'Yes' or 'No'.")



open("./src/data_store/DeterministicFields.json", "w").write(json.dumps(determisitic_data, indent=4))