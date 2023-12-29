from unittest.mock import patch, MagicMock
from chalice.test import Client
from app import *
import json
from botocore.stub import Stubber
from chalicelib.db import DynamoDB


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
            response_all = client.http.get('/reset/all')
            assert response_all.status_code == 200
            assert response_all.body.decode('utf-8') == 'everything is deleted'

        mock_delete.assert_called()


def simulating_s3_response(sudo_bucket_name, test_pdf_file_path, file_name):
    try:
        with open(test_pdf_file_path, 'rb') as pdf_file:
            pdf_binary_data = pdf_file.read()
    except FileNotFoundError:
        print(f"File '{test_pdf_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    class DummyObject:
        def read(self):
            return pdf_binary_data

    s3_client = get_s3_client()

    stub = Stubber(s3_client)
    stub.add_response(
        'get_object',
        expected_params={'Bucket': sudo_bucket_name, 'Key': file_name},
        service_response={
            'Body': DummyObject()
        }
    )

    return stub


def check_stored_info(*args, **kwargs):
    assert args and isinstance(args[0], str) and args[0], "dataid must be a non-empty string"
    assert 'info' in kwargs and isinstance(kwargs['info'], str) and kwargs['info'], "datastr must be a non-empty " \
                                                                                    "string "


def run_test(sudo_bucket_name, test_pdf_file_path, file_name):
    stub = simulating_s3_response(sudo_bucket_name, test_pdf_file_path, file_name)
    with stub:
        with Client(app) as client:
            magic_check_stored_info = MagicMock(side_effect=check_stored_info)
            DynamoDB.add_file = magic_check_stored_info
            event = client.events.generate_s3_event(bucket=sudo_bucket_name, key=file_name)
            client.lambda_.invoke('handle_object_created', event)
            magic_check_stored_info.assert_called()


def test_handle_object_created():

    # Define your parameters
    sudo_bucket_name = 'test_bucket'
    test_pdf_file_path = 'tests/data/Zhuolun_Du_2023.pdf'
    file_name = test_pdf_file_path.split('/')[-1]

    # Call the run_test method
    run_test(sudo_bucket_name, test_pdf_file_path, file_name)

