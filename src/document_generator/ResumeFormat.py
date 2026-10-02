# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: ResumeFormat
# Project Description: Defines the structured ouput for LLM to generate resume content


from pydantic import BaseModel, Field

class PersonalDetails(BaseModel):
    name: str
    number: str
    location: str
    linkedin: str 
    github: str
    website: str
    
class BulletFormat(BaseModel):
    bullet = Field()

class WorkEntry(BaseModel):
    title: str
    company: str 
    start_date: str
    end_date: str
    bullet_points: list[BulletFormat] = Field("First BulletFormat Objects should be most relevant")
    

class ResumeFormat(BaseModel):
    personal_details: PersonalDetails       # (filled in from deterministically)
    personal_summary: str
    work_experience: list[WorkEntry]
    relevant_projects: list[ProjectEntry]
    relevant_skills: list[str]