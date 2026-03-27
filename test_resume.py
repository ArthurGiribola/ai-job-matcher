from app.services.resume_parser import parse_resume_file

result = parse_resume_file("data/tests/test.txt")

print("SKILLS ENCONTRADAS:")
print(result["skills"])