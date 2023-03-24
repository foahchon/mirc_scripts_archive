import datetime
import os
from flask import render_template, request, redirect
from app import app
import models

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', scripts=models.mIRCScript.query.order_by(models.mIRCScript.name).all())

@app.route('/submit_script', methods=['GET'])
def submit_script():
    return render_template('submit_script.html')

@app.route('/submit_script', methods=['POST'])
def upload_script():
    all_form_keys = {'name', 'author', 'version', 'year', 'description', 'submitter'}

    invalid_fields = set(filter(lambda x: x not in request.form or len(request.form[x]) <= 0, all_form_keys))
    if not request.files['file']:
        invalid_fields.add('file')
    if len(invalid_fields) > 0:
        return render_template('submit_script.html', **request.form, invalid_fields=invalid_fields)
    else:
        uploaded_file = request.files['file']
        uploaded_file.save(f'../uploads/{uploaded_file.filename}')

        script_submission = models.ScriptSubmission(
            name=request.form['name'],
            author=request.form['author'],
            version=request.form['version'],
            year=request.form['year'],
            description=request.form['description'],
            submitter=request.form['submitter'],
            upload_path=f'../uploads/{uploaded_file.filename}'
        )

        models.db.session.add(script_submission)
        models.db.session.commit()

        return render_template('thank_you.html')
    
@app.route('/view_script_version/<int:version_id>', methods=['GET'])
def view_script_version(version_id):
    script_version = models.ScriptVersion.query.filter_by(id=version_id).first_or_404()
    other_versions = models.ScriptVersion.query \
        .filter(models.ScriptVersion.script_id == script_version.script_id) \
        .filter(models.ScriptVersion.id != script_version.id).order_by(models.ScriptVersion.version_number.desc())
    
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
    submissions = models.ScriptSubmission.query.all()

    return render_template('view_submissions_queue.html', submissions=submissions)

@app.route('/view_submission_detail/<int:submission_id>')
def view_submission_detail(submission_id):
    submission = models.ScriptSubmission.query.filter_by(id=submission_id).first_or_404()

    return render_template('view_submission_detail.html', submission=submission)

@app.route('/approve_submission<int:submission_id>', methods=['POST'])
def approve_submission(submission_id):
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