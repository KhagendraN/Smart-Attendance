import qrcode
from io import BytesIO
import base64
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from models import Class, Student, Attendance, Subject, db, User
from datetime import datetime
from sheets import GoogleSheetsManager
from sqlalchemy.orm import joinedload
import os

attendance_bp = Blueprint('attendance', __name__)
sheets_manager = GoogleSheetsManager()

@attendance_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        teacher_subjects = Subject.query.filter(
            Subject.teachers.any(id=current_user.id)
        ).all()
        class_ids = set(subject.class_id for subject in teacher_subjects)
        classes = Class.query.filter(Class.id.in_(class_ids)).all()
    elif current_user.role == 'cr':
        classes = Class.query.filter_by(cr_id=current_user.id).all()
    else:
        classes = Class.query.all()

    return render_template('dashboard.html', classes=classes)

@attendance_bp.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    if request.method == 'POST':
        if current_user.role != 'cr':
            return jsonify({'error': 'Only CRs can create classes'}), 403

        name = request.form.get('name')
        new_class = Class(name=name, cr_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully', 'success')

    if current_user.role == 'cr':
        classes = Class.query.filter_by(cr_id=current_user.id).all()
    else:
        classes = []
    return render_template('classes.html', classes=classes)

@attendance_bp.route('/class/<int:class_id>/manage', methods=['GET', 'POST'])
@login_required
def manage_class(class_id):
    class_obj = Class.query.get_or_404(class_id)

    # Only CR can manage their own classes
    if current_user.role != 'cr' or class_obj.cr_id != current_user.id:
        flash('You do not have permission to manage this class', 'danger')
        return redirect(url_for('attendance.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_subject':
            subject_name = request.form.get('subject_name')
            teacher_names = request.form.getlist('teacher_names[]')
            teacher_emails = request.form.getlist('teacher_emails[]')

            # Create new subject
            subject = Subject(name=subject_name, class_id=class_id)
            db.session.add(subject)

            # Create teachers if they don't exist and add them to the subject
            for name, email in zip(teacher_names, teacher_emails):
                teacher = User.query.filter_by(email=email).first()
                if not teacher:
                    # Create new teacher
                    username = email.split('@')[0]  # Use email prefix as username
                    teacher = User(username=username, email=email, role='teacher')
                    teacher.set_password('temporary_password')  # They can reset this later
                    db.session.add(teacher)
                subject.teachers.append(teacher)

            db.session.commit()
            flash('Subject and teachers added successfully', 'success')

        elif action == 'add_student':
            name = request.form.get('student_name')
            roll_number = request.form.get('roll_number')

            # Check if roll number already exists in this class
            existing_student = Student.query.filter_by(
                class_id=class_id, roll_number=roll_number
            ).first()

            if existing_student:
                flash('A student with this roll number already exists', 'danger')
            else:
                student = Student(name=name, roll_number=roll_number, class_id=class_id)
                db.session.add(student)
                db.session.commit()
                flash('Student added successfully', 'success')

        elif action == 'delete_subject':
            subject_id = request.form.get('subject_id')
            subject = Subject.query.get_or_404(subject_id)
            if subject.class_id == class_id:
                db.session.delete(subject)
                db.session.commit()
                flash('Subject deleted successfully', 'success')

        elif action == 'delete_student':
            student_id = request.form.get('student_id')
            student = Student.query.get_or_404(student_id)
            if student.class_id == class_id:
                db.session.delete(student)
                db.session.commit()
                flash('Student deleted successfully', 'success')

        elif action == 'delete_class':
            # Delete the class and all related records
            db.session.delete(class_obj)
            db.session.commit()
            flash('Class deleted successfully', 'success')
            return redirect(url_for('attendance.classes'))

    # Get all teachers for display
    teachers = User.query.filter_by(role='teacher').all()

    return render_template('manage_class.html', 
                         class_obj=class_obj,
                         teachers=teachers)

@attendance_bp.route('/attendance/<int:class_id>', methods=['GET', 'POST'])
@login_required
def mark_attendance(class_id):
    class_obj = Class.query.get_or_404(class_id)
    subjects = Subject.query.filter_by(class_id=class_id).all()

    if request.method == 'POST':
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        subject_id = request.form.get('subject_id')
        teacher_id = request.form.get('teacher_id')
        attendance_data = []

        for student in class_obj.students:
            status = request.form.get(f'student_{student.id}') == 'present'
            attendance = Attendance(
                student_id=student.id,
                class_id=class_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                date=date,
                status=status,
                marked_by=current_user.id
            )
            db.session.add(attendance)
            attendance_data.append({
                'student_id': student.id,
                'student_name': student.name,
                'status': status
            })

        db.session.commit()
        sheets_manager.update_attendance(class_id, date, attendance_data)
        flash('Attendance marked successfully', 'success')

    return render_template('attendance.html', 
                         class_obj=class_obj, 
                         subjects=subjects,
                         today=datetime.now().strftime('%Y-%m-%d'))

@attendance_bp.route('/api/subject/<int:subject_id>/teachers')
@login_required
def get_subject_teachers(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    teachers = [{'id': t.id, 'username': t.username} for t in subject.teachers]
    return jsonify(teachers)

@attendance_bp.route('/reports/<int:class_id>')
@login_required
def reports(class_id):
    class_obj = Class.query.get_or_404(class_id)
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-01'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    try:
        attendance_data = sheets_manager.get_attendance_report(class_id, start_date, end_date)
        return render_template('reports.html', 
                            class_obj=class_obj, 
                            attendance_data=attendance_data,
                            start_date=start_date,
                            end_date=end_date)
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('attendance.dashboard'))

@attendance_bp.route('/download_report/<int:class_id>')
@login_required
def download_report(class_id):
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-01'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    try:
        file_path = sheets_manager.download_attendance_sheet(class_id, start_date, end_date)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'attendance_report_{class_id}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error downloading report: {str(e)}', 'danger')
        return redirect(url_for('attendance.reports', class_id=class_id))

@attendance_bp.route('/generate_qr/<int:class_id>')
@login_required
def generate_qr(class_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f'/attendance/{class_id}')
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({'qr_code': img_str})