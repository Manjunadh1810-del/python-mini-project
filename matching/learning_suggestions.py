"""
Curated skill -> suggested learning topics mapping, used by the Skill Gap
Analysis feature. For any skill not explicitly listed, a sensible generic
suggestion is generated instead of leaving the candidate with nothing.
"""

LEARNING_SUGGESTIONS = {
    'python': ['Python Programming Basics', 'Python for Backend Development', 'Object-Oriented Python'],
    'django': ['Django Fundamentals', 'Django REST Framework', 'Django ORM Deep Dive'],
    'django rest framework': ['Django REST Framework', 'Building APIs with DRF', 'API Authentication with DRF'],
    'flask': ['Flask Fundamentals', 'Building REST APIs with Flask'],
    'fastapi': ['FastAPI Crash Course', 'Async APIs with FastAPI'],
    'javascript': ['JavaScript Fundamentals', 'Modern ES6+ JavaScript', 'Asynchronous JavaScript'],
    'typescript': ['TypeScript Fundamentals', 'TypeScript with React'],
    'react': ['React Fundamentals', 'React Hooks and State Management', 'Building SPAs with React'],
    'node.js': ['Node.js Fundamentals', 'Building APIs with Express.js'],
    'sql': ['SQL Fundamentals', 'Database Design Principles', 'Advanced SQL Queries'],
    'mysql': ['MySQL for Developers', 'Database Design with MySQL'],
    'postgresql': ['PostgreSQL Fundamentals', 'Advanced PostgreSQL Features'],
    'mongodb': ['MongoDB Basics', 'NoSQL Database Design'],
    'rest api': ['REST API Development', 'API Design Principles', 'Postman for API Testing'],
    'restful api': ['REST API Development', 'API Design Principles'],
    'git': ['Git & GitHub Basics', 'Version Control Best Practices', 'Git Branching Strategies'],
    'docker': ['Docker Fundamentals', 'Containerization for Developers'],
    'kubernetes': ['Kubernetes Basics', 'Container Orchestration Fundamentals'],
    'aws': ['AWS Cloud Practitioner Basics', 'AWS for Backend Developers'],
    'azure': ['Microsoft Azure Fundamentals', 'Azure for Developers'],
    'machine learning': ['Machine Learning Fundamentals', 'Scikit-learn Practical Course', 'ML Model Deployment'],
    'deep learning': ['Deep Learning Specialization', 'Neural Networks Fundamentals'],
    'tensorflow': ['TensorFlow for Beginners', 'Building Models with TensorFlow'],
    'pytorch': ['PyTorch Fundamentals', 'Deep Learning with PyTorch'],
    'pandas': ['Data Analysis with Pandas', 'Pandas for Data Cleaning'],
    'numpy': ['NumPy Fundamentals', 'Numerical Computing with NumPy'],
    'data analysis': ['Data Analysis Fundamentals', 'Exploratory Data Analysis Techniques'],
    'data science': ['Data Science Fundamentals', 'Statistics for Data Science'],
    'html': ['HTML5 Fundamentals', 'Semantic HTML Best Practices'],
    'css': ['CSS Fundamentals', 'Responsive Design with CSS', 'Flexbox and Grid'],
    'bootstrap': ['Bootstrap 5 Crash Course', 'Responsive UI with Bootstrap'],
    'linux': ['Linux Command Line Basics', 'Linux System Administration'],
    'agile': ['Agile Methodology Fundamentals', 'Scrum Framework Basics'],
    'communication': ['Professional Communication Skills', 'Technical Writing Basics'],
    'leadership': ['Leadership Fundamentals', 'Team Management Basics'],
}


def get_learning_suggestions(skill_name):
    """Return 2-3 suggested learning topics for a given skill name."""
    key = skill_name.lower().strip()
    if key in LEARNING_SUGGESTIONS:
        return LEARNING_SUGGESTIONS[key]
    return [f"{skill_name} Fundamentals", f"Hands-on {skill_name} Projects"]
