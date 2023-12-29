from chalice import Chalice
from chalice import Rate
from chalicelib import db
from chalicelib import extract_pdf
from chalicelib.apify_scrapper import JobScraper
import os
import boto3
import io

app = Chalice(app_name='job_match')

# tem for pytest TODO: del after
os.environ['RESUME_BUCKET_NAME'] = "job-match-resumebucket-ygndex4ohi8p"
os.environ['JOB_TABLE_NAME'] = "job-match-JobTable-K36364VHXURZ"
os.environ['RESUME_TABLE_NAME'] = "job-match-ResumeTable-17EXYAJXU52JT"

_JOB_DB = None
_RESUME_DB = None
_S3_CLIENT = None

_SUPPORTED_FILE_EXTENSIONS = (
    '.pdf',
)


def get_job_db():
    global _JOB_DB
    if _JOB_DB is None:
        _JOB_DB = db.DynamoDB(
            boto3.resource('dynamodb').Table(
                os.environ['JOB_TABLE_NAME']), 'JobID')
    return _JOB_DB


def get_resume_db():
    global _RESUME_DB
    if _RESUME_DB is None:
        _RESUME_DB = db.DynamoDB(
            boto3.resource('dynamodb').Table(
                os.environ['RESUME_TABLE_NAME']), 'ResumeID')
    return _RESUME_DB


def get_s3_client():
    global _S3_CLIENT
    if _S3_CLIENT is None:
        _S3_CLIENT = boto3.client('s3')
    return _S3_CLIENT


@app.route('/')
def index():
    return "hello, this is default page"


@app.route('/list/job')
def get_job_file():
    return get_job_db().list_all()


@app.route('/list/resume')
def get_resume_file():
    return get_resume_db().list_all()


def delete_all():
    get_resume_db().delete_all()
    get_job_db().delete_all()


@app.route('/reset/all')
def reset():
    delete_all()
    return 'everything is deleted'


@app.route('/reset/job')
def reset():
    get_job_db().delete_all()
    return 'jobs are deleted'


@app.route('/reset/resume')
def reset():
    get_resume_db().delete_all()
    return 'resumes are deleted'


def _is_pdf(key):
    return key.endswith(_SUPPORTED_FILE_EXTENSIONS)


@app.on_s3_event(bucket=os.environ['RESUME_BUCKET_NAME'],
                 events=['s3:ObjectCreated:*'])
def handle_object_created(event):
    if _is_pdf(event.key):
        s3_client = get_s3_client()
        bucket_name = event.bucket

        # Get the file object from S3
        file_obj = s3_client.get_object(Bucket=bucket_name, Key=event.key)

        # Read the PDF file into a BytesIO object
        file_content = io.BytesIO(file_obj['Body'].read())

        resume_str = extract_pdf.extract_text_from_pdf(file_content)

        get_resume_db().add_file(
            db.generate_unique_id(),
            info=resume_str
        )
    else:
        # TODO: add ability to handel other type of file or warn user file type is no supported
        pass


# @app.schedule(Rate(1, unit=Rate.MINUTES))
# def every_one_min(event):
#     get_job_db().add_file(
#         db.generate_unique_id(),
#         info='some job info'
#     )

# @app.schedule(Rate(1, unit=Rate.DAYS))
@app.route('/test_scrapping')
def job_scrapping():
    api_token = "apify_api_UTzABhZjVPwwd0v3zfj7ipY7co3eJ04loR1L"
    actor_id = "deM7vgccGPS1CLYwV"

    run_input = {
        "keyword": "Cloud Data Engineer",
        "location": "California",
        "showRemoteJobs": True,
        "showFullTime": True,
        "showPartTime": True,
        "showTemporary": True,
        "showIntern": True,
        "useApifyProxy": False,
    }

    js = JobScraper(api_token, actor_id, **run_input)
    print('____________________scrapping starts______________________________')
    js.run_scraper()
    js.save_job_results_to_db(get_job_db())
    print('_____________________scrapping ends ______________________________')
