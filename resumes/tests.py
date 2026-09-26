import io
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User
from candidates.models import CandidateProfile
from .models import Resume
from .services import extract_text_from_pdf, extract_text_from_docx, extract_text, ResumeExtractionError


def _make_test_pdf_bytes(text="John Doe\nPython Developer\nSkills: Python, Django, SQL"):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 20
    c.save()
    buf.seek(0)
    return buf.read()


def _make_test_docx_bytes(text="Jane Smith\nML Engineer\nSkills: Python, TensorFlow"):
    from docx import Document
    buf = io.BytesIO()
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(buf)
    buf.seek(0)
    return buf.read()


class ExtractionServiceTests(TestCase):
    def test_extract_text_from_valid_pdf(self):
        pdf_bytes = _make_test_pdf_bytes()
        text = extract_text_from_pdf(io.BytesIO(pdf_bytes))
        self.assertIn("Python", text)
        self.assertIn("Django", text)

    def test_extract_text_from_valid_docx(self):
        docx_bytes = _make_test_docx_bytes()
        text = extract_text_from_docx(io.BytesIO(docx_bytes))
        self.assertIn("TensorFlow", text)

    def test_extract_text_dispatcher_pdf(self):
        pdf_bytes = _make_test_pdf_bytes()
        text = extract_text(io.BytesIO(pdf_bytes), 'pdf')
        self.assertIn("Python", text)

    def test_extract_text_unsupported_type_raises(self):
        with self.assertRaises(ResumeExtractionError):
            extract_text(io.BytesIO(b"whatever"), 'txt')

    def test_corrupt_pdf_raises_extraction_error(self):
        with self.assertRaises(ResumeExtractionError):
            extract_text_from_pdf(io.BytesIO(b"not a real pdf"))

    def test_corrupt_docx_raises_extraction_error(self):
        with self.assertRaises(ResumeExtractionError):
            extract_text_from_docx(io.BytesIO(b"not a real docx file"))

    def test_pdf_with_no_text_layer_raises_extraction_error(self):
        # A PDF with a page but no drawn text (simulates a scanned/image-only PDF).
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.showPage()  # blank page, no text
        c.save()
        buf.seek(0)
        with self.assertRaises(ResumeExtractionError):
            extract_text_from_pdf(buf)


class ResumeUploadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_resume', email='candresume@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(user=self.candidate)
        self.client.login(username='cand_resume', password='pass12345')

    def test_upload_valid_pdf_resume(self):
        pdf_bytes = _make_test_pdf_bytes()
        uploaded = SimpleUploadedFile("resume.pdf", pdf_bytes, content_type="application/pdf")
        response = self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        self.assertEqual(response.status_code, 302)
        resume = Resume.objects.get(candidate=self.profile)
        self.assertTrue(resume.extraction_successful)
        self.assertIn("Python", resume.extracted_text)

    def test_reject_invalid_file_extension(self):
        uploaded = SimpleUploadedFile("resume.txt", b"plain text resume", content_type="text/plain")
        response = self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        self.assertFalse(Resume.objects.filter(candidate=self.profile).exists())

    def test_reject_oversized_file(self):
        # 6 MB fake pdf content (limit is 5 MB)
        big_content = b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024)
        uploaded = SimpleUploadedFile("big.pdf", big_content, content_type="application/pdf")
        response = self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resume.objects.filter(candidate=self.profile).exists())

    def test_reupload_replaces_existing_resume(self):
        pdf1 = SimpleUploadedFile("r1.pdf", _make_test_pdf_bytes("First Resume Python"), content_type="application/pdf")
        self.client.post(reverse('resumes:resume_upload'), {'file': pdf1})
        self.assertEqual(Resume.objects.filter(candidate=self.profile).count(), 1)

        pdf2 = SimpleUploadedFile("r2.pdf", _make_test_pdf_bytes("Second Resume Django"), content_type="application/pdf")
        self.client.post(reverse('resumes:resume_upload'), {'file': pdf2})
        self.assertEqual(Resume.objects.filter(candidate=self.profile).count(), 1)
        resume = Resume.objects.get(candidate=self.profile)
        self.assertIn("Django", resume.extracted_text)

    def test_delete_resume(self):
        pdf = SimpleUploadedFile("r.pdf", _make_test_pdf_bytes(), content_type="application/pdf")
        self.client.post(reverse('resumes:resume_upload'), {'file': pdf})
        self.client.get(reverse('resumes:resume_delete'))
        self.assertFalse(Resume.objects.filter(candidate=self.profile).exists())

    def test_recruiter_cannot_upload_resume(self):
        recruiter = User.objects.create_user(
            username='recr_resume', email='recrresume@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.client.logout()
        self.client.login(username='recr_resume', password='pass12345')
        response = self.client.get(reverse('resumes:resume_upload'))
        self.assertRedirects(response, reverse('home'))

    def test_upload_valid_extension_but_corrupt_content_saves_with_extraction_failed(self):
        # Passes form validation (valid .pdf extension) but pypdf can't parse the bytes -
        # exercises the except ResumeExtractionError branch in the view.
        uploaded = SimpleUploadedFile("broken.pdf", b"not really a pdf file content here", content_type="application/pdf")
        response = self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        self.assertEqual(response.status_code, 302)
        resume = Resume.objects.get(candidate=self.profile)
        self.assertFalse(resume.extraction_successful)
        self.assertTrue(resume.extraction_error)

    def test_resume_view_with_no_resume_redirects_to_upload(self):
        response = self.client.get(reverse('resumes:resume_view'))
        self.assertRedirects(response, reverse('resumes:resume_upload'))

    def test_resume_analysis_with_no_resume_redirects_to_upload(self):
        response = self.client.get(reverse('resumes:resume_analysis'))
        self.assertRedirects(response, reverse('resumes:resume_upload'))

    def test_resume_analysis_blocked_when_extraction_failed(self):
        uploaded = SimpleUploadedFile("broken2.pdf", b"garbage content not a pdf", content_type="application/pdf")
        self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        response = self.client.get(reverse('resumes:resume_analysis'))
        self.assertRedirects(response, reverse('resumes:resume_view'))


class ResumeAnalyzerTests(TestCase):
    def test_extract_skills_from_text_matches_known_keywords(self):
        from resumes.analyzer import extract_skills_from_text
        text = "Experienced in Python, Django, and Machine Learning. Familiar with SQL and Git."
        skills = extract_skills_from_text(text)
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('Machine Learning', skills)
        self.assertIn('SQL', skills)
        self.assertIn('Git', skills)

    def test_extract_skills_avoids_partial_word_matches(self):
        from resumes.analyzer import extract_skills_from_text
        # "Java" should not match inside "JavaScript" incorrectly excluding JavaScript itself,
        # and "R" should not match inside random words.
        text = "I know JavaScript and worked with Reactive programming concepts."
        skills = extract_skills_from_text(text)
        self.assertIn('JavaScript', skills)
        # 'R' (the language) should not spuriously match inside 'Reactive'
        self.assertNotIn('R', skills)

    def test_extract_education_hints_finds_degree_lines(self):
        from resumes.analyzer import extract_education_hints
        text = "John Doe\nB.Tech in Computer Science, XYZ University, 2020-2024\nSkills: Python"
        hints = extract_education_hints(text)
        self.assertTrue(any('B.Tech' in h for h in hints))

    def test_extract_experience_years_hint(self):
        from resumes.analyzer import extract_experience_years_hint
        text = "I have 3 years of experience in backend development."
        years = extract_experience_years_hint(text)
        self.assertEqual(years, 3.0)

    def test_extract_experience_years_hint_none_when_absent(self):
        from resumes.analyzer import extract_experience_years_hint
        text = "Fresh graduate looking for opportunities."
        self.assertIsNone(extract_experience_years_hint(text))


class ResumeAnalysisViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_analysis', email='candanalysis@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(user=self.candidate)
        self.client.login(username='cand_analysis', password='pass12345')

        pdf_bytes = _make_test_pdf_bytes("Skills: Python, Django, SQL, Machine Learning")
        uploaded = SimpleUploadedFile("resume.pdf", pdf_bytes, content_type="application/pdf")
        self.client.post(reverse('resumes:resume_upload'), {'file': uploaded})
        self.resume = Resume.objects.get(candidate=self.profile)

    def test_analysis_runs_automatically_on_upload(self):
        self.assertTrue(self.resume.is_analyzed())
        self.assertIn('Python', self.resume.extracted_skills)

    def test_analysis_page_loads(self):
        response = self.client.get(reverse('resumes:resume_analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python')

    def test_add_extracted_skills_to_profile(self):
        from candidates.models import CandidateSkill
        self.assertEqual(CandidateSkill.objects.filter(candidate=self.profile).count(), 0)
        response = self.client.post(reverse('resumes:add_extracted_skills'))
        self.assertEqual(response.status_code, 302)
        added_names = set(CandidateSkill.objects.filter(candidate=self.profile).values_list('skill__name', flat=True))
        self.assertIn('Python', added_names)
        self.assertIn('Django', added_names)

    def test_add_extracted_skills_does_not_duplicate(self):
        from candidates.models import CandidateSkill, Skill
        skill = Skill.objects.create(name='Python')
        CandidateSkill.objects.create(candidate=self.profile, skill=skill, proficiency='expert')

        self.client.post(reverse('resumes:add_extracted_skills'))
        python_entries = CandidateSkill.objects.filter(candidate=self.profile, skill__name__iexact='Python')
        self.assertEqual(python_entries.count(), 1)
        self.assertEqual(python_entries.first().proficiency, 'expert')  # unchanged, not overwritten

    def test_reanalyze_updates_timestamp(self):
        original_time = self.resume.analyzed_at
        response = self.client.get(reverse('resumes:resume_reanalyze'))
        self.assertEqual(response.status_code, 302)
        self.resume.refresh_from_db()
        self.assertGreaterEqual(self.resume.analyzed_at, original_time)
