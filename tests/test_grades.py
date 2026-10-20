import unittest
from decimal import Decimal
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import User, Classroom, Enrollment, Assignment, Grade
from app.routes.grades import save_grade, list_grades, roster
from app.schemas.grade import GradeInput

class GradeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.teacher = User(id=1,email='t@test.edu',password_hash='x',name='Teacher',role='teacher',is_active=True)
        self.other_teacher = User(id=2,email='t2@test.edu',password_hash='x',name='Other teacher',role='teacher',is_active=True)
        self.student = User(id=3,email='s@test.edu',password_hash='x',name='Student',role='student',is_active=True)
        self.other_student = User(id=4,email='s2@test.edu',password_hash='x',name='Other student',role='student',is_active=True)
        self.db.add_all([self.teacher,self.other_teacher,self.student,self.other_student,
            Classroom(id=1,teacher_id=1,name='Finance'),Classroom(id=2,teacher_id=2,name='Other class'),
            Enrollment(classroom_id=1,student_id=3,status='active'),Enrollment(classroom_id=1,student_id=4,status='active'),
            Assignment(id=1,classroom_id=1,created_by=1,title='Budget',status='active'),
            Assignment(id=2,classroom_id=2,created_by=2,title='Other assignment',status='active')])
        self.db.commit()
    def tearDown(self):
        self.db.close(); self.engine.dispose()
    def payload(self, **updates):
        return GradeInput(**({'assignment_id':1,'student_id':3,'points_earned':'85.25','points_possible':'100','feedback':'Good work'} | updates))
    def test_teacher_can_save_and_student_can_read(self):
        save_grade(self.payload(),self.db,self.teacher)
        result=list_grades(None,self.db,self.student)
        self.assertEqual(len(result),1); self.assertEqual(result[0]['points_earned'],'85.25')
        self.assertEqual(result[0]['feedback'],'Good work'); self.assertEqual(result[0]['assignment_title'],'Budget')
    def test_update_does_not_duplicate_grade(self):
        save_grade(self.payload(),self.db,self.teacher)
        save_grade(self.payload(points_earned='90'),self.db,self.teacher)
        self.assertEqual(self.db.query(Grade).count(),1)
        self.assertEqual(list_grades(None,self.db,self.student)[0]['points_earned'],'90.00')
    def test_students_only_see_their_own_grades(self):
        save_grade(self.payload(),self.db,self.teacher)
        save_grade(self.payload(student_id=4,points_earned='70'),self.db,self.teacher)
        result=list_grades(None,self.db,self.student)
        self.assertEqual([g['student_id'] for g in result],[3])
    def test_other_teacher_cannot_read_or_write(self):
        save_grade(self.payload(),self.db,self.teacher)
        self.assertEqual(list_grades(None,self.db,self.other_teacher),[])
        with self.assertRaises(HTTPException) as result: save_grade(self.payload(),self.db,self.other_teacher)
        self.assertEqual(result.exception.status_code,403)
        with self.assertRaises(HTTPException): roster(1,self.db,self.other_teacher)
    def test_non_enrolled_and_archived_students_rejected(self):
        with self.assertRaises(HTTPException): save_grade(self.payload(assignment_id=2),self.db,self.other_teacher)
        enrollment=self.db.query(Enrollment).filter_by(student_id=3).one(); enrollment.status='archived'; self.db.commit()
        with self.assertRaises(HTTPException): save_grade(self.payload(),self.db,self.teacher)
    def test_roster_only_has_active_enrolled_students(self):
        data=roster(1,self.db,self.teacher)
        self.assertEqual([s['id'] for s in data['students']],[4,3])
        self.assertEqual([a['id'] for a in data['assignments']],[1])
    def test_invalid_points_rejected(self):
        for updates in [{'points_earned':'-1'},{'points_earned':'101'},{'points_possible':'0'},
                        {'points_earned':'NaN'},{'points_earned':'Infinity'},{'points_earned':'1.001'}]:
            with self.subTest(updates=updates):
                with self.assertRaises(ValidationError): self.payload(**updates)
    def test_zero_score_is_valid(self):
        save_grade(self.payload(points_earned='0'),self.db,self.teacher)
        self.assertEqual(Decimal(list_grades(None,self.db,self.student)[0]['points_earned']),0)
    def test_empty_gradebook(self):
        self.assertEqual(list_grades(None,self.db,self.student),[])

if __name__=='__main__': unittest.main()
