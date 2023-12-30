from unittest.mock import patch, Mock, MagicMock
from chalice.test import Client
from app import *
import json
from botocore.stub import Stubber
from chalicelib.db import DynamoDB
from pytest import fixture


@fixture
def client():
    with Client(app, stage_name='dev') as client:
        yield client


def test_index(client):
    response = client.http.get('/')
    assert response.status_code == 200
    assert response.body.decode('utf-8') == 'hello, this is default page'


def test_get_job_file(client):
    response = client.http.get('/list/job')
    assert response.status_code == 200
    job_list = json.loads(response.body.decode('utf-8'))
    assert isinstance(job_list, list)


def test_get_resume_file(client):
    response = client.http.get('/list/resume')
    assert response.status_code == 200
    resume_list = json.loads(response.body.decode('utf-8'))
    assert isinstance(resume_list, list)


@fixture
def mock_get_resume_db():
    with patch('app.get_resume_db') as mock:
        yield mock


@fixture
def mock_get_job_db():
    with patch('app.get_job_db') as mock:
        yield mock


def test_deletes(client, mock_get_resume_db, mock_get_job_db):
    mock_resume_db = Mock()
    mock_job_db = Mock()

    mock_get_resume_db.return_value = mock_resume_db
    mock_get_job_db.return_value = mock_job_db

    response_all = client.http.get('/delete/all')
    assert response_all.status_code == 200
    assert response_all.body.decode('utf-8') == 'everything is deleted'

    response_resume = client.http.get('/delete/resume')
    assert response_resume.status_code == 200
    assert response_resume.body.decode('utf-8') == 'resumes are deleted'

    response_job = client.http.get('/delete/job')
    assert response_job.status_code == 200
    assert response_job.body.decode('utf-8') == 'jobs are deleted'

    assert mock_get_resume_db.call_count == 2
    assert mock_get_job_db.call_count == 2
    assert mock_resume_db.delete_all.call_count == 2
    assert mock_job_db.delete_all.call_count == 2


sudo_bucket_name = 'test_bucket'
test_pdf_file_path = 'tests/data/Zhuolun_Du_2023.pdf'
file_name = test_pdf_file_path.split('/')[-1]


@fixture
def s3_response_stub():
    try:
        with open(test_pdf_file_path, 'rb') as pdf_file:
            pdf_binary_data = pdf_file.read()
    except FileNotFoundError:
        print(f"File '{test_pdf_file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

    file_obj = Mock()
    file_obj.read.return_value = pdf_binary_data

    s3_client = get_s3_client()
    stub = Stubber(s3_client)

    with stub:
        stub.add_response(
            'get_object',
            expected_params={'Bucket': sudo_bucket_name, 'Key': file_name},
            service_response={
                'Body': file_obj
            }
        )
        yield stub


def check_stored_info(*args, **kwargs):
    assert args and isinstance(args[0], str) and args[0], "dataid must be a non-empty string"
    assert 'info' in kwargs and isinstance(kwargs['info'], str) and kwargs['info'], "datastr must be a non-empty " \
                                                                                    "string "


def test_handle_object_created(s3_response_stub, client):
    magic_check_stored_info = MagicMock(side_effect=check_stored_info)
    DynamoDB.add_file = magic_check_stored_info
    event = client.events.generate_s3_event(bucket=sudo_bucket_name, key=file_name)
    client.lambda_.invoke('handle_object_created', event)
    magic_check_stored_info.assert_called()
