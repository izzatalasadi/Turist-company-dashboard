import unittest
from name_search_engine.manage import app, db  

import os
class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        print("Current Working Directory:", os.getcwd())
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.db'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_excel_upload(self):
        # Assuming you have a test Excel file named 'test_file.xlsx'
        path_to_excel_file = 'test.xlsx'
        with open(path_to_excel_file, 'rb') as test_file:
            response = self.app.post('/', data={
                'file': (test_file, 'test.xlsx')
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            # Additional assertions based on your application's response

if __name__ == '__main__':
    unittest.main()
