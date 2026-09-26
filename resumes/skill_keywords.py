"""
Curated dictionary of common skill keywords used to seed resume skill
extraction, in addition to whatever is already in the live Skill catalog
(candidates.models.Skill). This ensures matching works well even on a
fresh install before many candidates/jobs have populated the catalog.

Kept as plain data so it's easy to extend without touching extraction logic.
"""

PROGRAMMING_LANGUAGES = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C', 'C++', 'C#', 'Go', 'Rust',
    'PHP', 'Ruby', 'Kotlin', 'Swift', 'R', 'MATLAB', 'Scala', 'Perl', 'Dart',
]

WEB_FRAMEWORKS = [
    'Django', 'Django REST Framework', 'Flask', 'FastAPI', 'React', 'Angular', 'Vue.js',
    'Node.js', 'Express.js', 'Spring Boot', 'Spring', 'ASP.NET', 'Laravel', 'Ruby on Rails',
    'Bootstrap', 'Tailwind CSS', 'jQuery', 'Next.js',
]

DATABASES = [
    'SQL', 'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Oracle', 'Microsoft SQL Server',
    'Cassandra', 'DynamoDB', 'Firebase', 'NoSQL',
]

DATA_ML_AI = [
    'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'NLP', 'Computer Vision',
    'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy', 'Data Analysis',
    'Data Science', 'Data Visualization', 'Matplotlib', 'Seaborn', 'OpenCV', 'Artificial Intelligence',
    'Statistics', 'Big Data', 'Hadoop', 'Spark', 'Power BI', 'Tableau',
]

DEVOPS_CLOUD = [
    'Git', 'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Google Cloud Platform', 'GCP',
    'CI/CD', 'Jenkins', 'Linux', 'Bash', 'Shell Scripting', 'Terraform', 'Ansible', 'Nginx', 'Apache',
]

APIS_TOOLS = [
    'REST API', 'RESTful API', 'GraphQL', 'API Development', 'Microservices', 'JSON', 'XML',
    'Postman', 'JIRA', 'Agile', 'Scrum', 'Unit Testing', 'Pytest', 'Selenium', 'JUnit',
    'Object-Oriented Programming', 'OOP', 'Data Structures', 'Algorithms',
]

SOFT_SKILLS = [
    'Communication', 'Teamwork', 'Leadership', 'Problem Solving', 'Time Management',
    'Critical Thinking', 'Project Management', 'Adaptability', 'Collaboration',
]

COMMON_SKILLS = (
    PROGRAMMING_LANGUAGES + WEB_FRAMEWORKS + DATABASES + DATA_ML_AI
    + DEVOPS_CLOUD + APIS_TOOLS + SOFT_SKILLS
)

DEGREE_KEYWORDS = [
    'B.Tech', 'B.E.', 'BE', 'M.Tech', 'M.E.', 'ME', 'MBA', 'BCA', 'MCA',
    'B.Sc', 'M.Sc', 'B.Com', 'M.Com', 'BBA', 'Ph.D', 'PhD', 'Diploma',
    'B.A.', 'M.A.', 'Bachelor of Technology', 'Master of Technology',
    'Bachelor of Engineering', 'Master of Engineering', 'Bachelor of Science',
    'Master of Science', 'Bachelor of Computer Applications', 'Master of Computer Applications',
]
