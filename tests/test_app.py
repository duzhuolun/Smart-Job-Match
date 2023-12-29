from unittest.mock import patch, MagicMock
from chalice.test import Client
from app import app, get_resume_db, extract_pdf
import json
import os
import io
import boto3
from botocore.stub import Stubber

os.environ['RESUME_BUCKET_NAME'] = "job-match-resumebucket-ygndex4ohi8p"
os.environ['JOB_TABLE_NAME'] = "job-match-JobTable-K36364VHXURZ"
os.environ['RESUME_TABLE_NAME'] = "job-match-ResumeTable-17EXYAJXU52JT"


def test_index():
    with Client(app, stage_name='dev') as client:
        response = client.http.get('/')
        assert response.status_code == 200
        assert response.body.decode('utf-8') == 'hello, this is default page'


def test_get_job_file():
    with Client(app) as client:
        response = client.http.get('/list/job')
        assert response.status_code == 200
        job_list = json.loads(response.body.decode('utf-8'))
        assert isinstance(job_list, list)


def test_get_resume_file():
    with Client(app) as client:
        response = client.http.get('/list/resume')
        assert response.status_code == 200
        resume_list = json.loads(response.body.decode('utf-8'))
        assert isinstance(resume_list, list)


def test_delete_all():
    with patch('app.delete_all') as mock_delete:
        mock_delete.return_value = None

        with Client(app) as client:
            response = client.http.get('/reset')
            assert response.status_code == 200
            assert response.body.decode('utf-8') == 'everything is deleted'

        mock_delete.assert_called()



