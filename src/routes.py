import datetime
import os
from flask import abort, render_template, request, redirect, url_for
from app import app
import boto3
import botocore
import models
from sqlalchemy.orm import joinedload

def make_s3_client():
    session = boto3.session.Session()


    client = session.client('s3',
                        # Find your endpoint in the control panel, under Settings. Prepend "https://".
                        endpoint_url=os.getenv('SPACES_ENDPOINT'),
                        # Configures to use subdomain/virtual calling format.
                        config=botocore.config.Config(
                            s3={'addressing_style': 'virtual'}),
                        region_name='nyc3',  # Use the region in your endpoint.
                        # Access key pair. You can create access key pairs using the control panel or API.
                        aws_access_key_id=os.getenv('SPACES_ACCESS_KEY'),
                        aws_secret_access_key=os.getenv('SPACES_SECRET_KEY'))  # Secret access key defined through an environment variable.
    
    return client

@app.route('/', methods=['GET'])
def index():
    scripts = models.mIRCScript.query.order_by(models.mIRCScript.name) \
        .options(joinedload(models.mIRCScript.author)) \
        .options(joinedload(models.mIRCScript.default_version)) \
        .all()
    
    return render_template('index.html', scripts=scripts)

@app.route('/submit_script', methods=['GET'])
def submit_script():
    return render_template('submit_script.html')

@app.route('/submit_script', methods=['POST'])
def upload_script():
    all_form_keys = {'name', 'author', 'version', 'year', 'submitter'}

    invalid_fields = set(filter(lambda x: x not in request.form or len(request.form[x]) <= 0, all_form_keys))
    if not request.files['file']:
        invalid_fields.add('file')
    if len(invalid_fields) > 0:
        return render_template('submit_script.html', **request.form, invalid_fields=invalid_fields)
    else:
        s3client = make_s3_client()
        uploaded_file = request.files['file']

        s3client.upload_fileobj(
            uploaded_file,
            'scripts',
            uploaded_file.filename,
            ExtraArgs={
                'ACL': 'private',
                'ContentType': uploaded_file.content_type
            }
        )

        script_submission = models.ScriptSubmission(
            name=request.form['name'],
            author=request.form['author'],
            version=request.form['version'],
            year=request.form['year'],
            description=request.form['description'],
            submitter=request.form['submitter'],
            upload_path=uploaded_file.filename
        )

        models.db.session.add(script_submission)
        models.db.session.commit()

        return render_template('thank_you.html')
    
@app.route('/view_script_version/<int:version_id>', methods=['GET'])
def view_script_version(version_id):
    script_version = models.ScriptVersion.query \
            .filter_by(id=version_id) \
            .options(joinedload(models.ScriptVersion.script)) \
            .first_or_404()
    other_versions = models.ScriptVersion.query \
        .filter(models.ScriptVersion.script_id == script_version.script_id) \
        .filter(models.ScriptVersion.id != script_version.id) \
        .order_by(models.ScriptVersion.version_number.desc())
    
    return render_template('view_script_version.html', script_version=script_version, other_versions=other_versions)

@app.route('/view_author/<int:author_id>')
def view_author(author_id):
    author = models.Author.query.filter_by(id=author_id).first_or_404()
    return render_template('view_author.html', author=author)

@app.route('/download_script/<int:version_id>', methods=['GET'])
def download_script(version_id):
    version = models.ScriptVersion.query.filter_by(id=version_id).first_or_404()
    version.script.download_count += 1

    models.db.session.commit()
    return redirect(f"{os.getenv('SCRIPTS_BUCKET_PREFIX')}{version.download_url}")

@app.route('/view_submissions_queue', methods=['GET'])
def view_submissions_queue():
    if os.getenv('PUBLIC_MODE'):
        return abort(404)

    submissions = models.ScriptSubmission.query.filter_by(approved_at=None)

    return render_template('view_submissions_queue.html', submissions=submissions)

@app.route('/view_submission_detail/<int:submission_id>')
def view_submission_detail(submission_id):
    if os.getenv('PUBLIC_MODE'):
        return abort(404)
    
    submission = models.ScriptSubmission.query.filter_by(id=submission_id).first_or_404()

    return render_template('view_submission_detail.html', submission=submission)

@app.route('/approve_submission/<int:submission_id>', methods=['POST'])
def approve_submission(submission_id):
    if os.getenv('PUBLIC_MODE'):
        return abort(404)

    submission = models.ScriptSubmission.query.filter_by(id=submission_id).first_or_404()

    script = models.mIRCScript.query.filter_by(name=submission.name).first()
    if not script:
        script = models.mIRCScript(
            name=submission.name,
            year=submission.year
        )

    author = models.Author.query.filter_by(name=submission.author).first()
    if not author:
        author = models.Author(
            name=submission.author
        )

    version = models.ScriptVersion(
        version_number=submission.version,
        description=submission.description,
        submitter=submission.submitter,
        download_url=submission.upload_path
    )

    script.author = author
    script.versions.append(version)
    submission.approved_at = datetime.datetime.utcnow()

    models.db.session.add(script)
    models.db.session.commit()

    if not script.default_version:
        script.default_version_id = version.id
    elif version.version_number > script.default_version.version_number:
        script.default_version_id = version.id

    models.db.session.commit()

    s3client = make_s3_client()
    s3client.put_object(Bucket='scripts', Key=submission.upload_path, ACL='public-read')

    return redirect(url_for('view_submissions_queue'))