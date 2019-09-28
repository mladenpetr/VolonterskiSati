from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException

from auth import login_required, savjetnik_required, admin_required

import Utilities

from constants import Iskaznice, AccessLevels

import datetime

from DatabaseController import DatabaseController, get_date_object
import DatabaseTables


members_bp = Blueprint('members', __name__, url_prefix='/members')


@members_bp.route('/add', methods=('GET', 'POST'))
@login_required
@savjetnik_required
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['lastname']
        nickname = request.form['nickname']
        oib = request.form['oib']
        phone_number = request.form['phone']
        date_of_birth = request.form['dateofbirth']
        membership_start = request.form['membership']
        card_id = request.form['idcard']
        email = request.form['email']
        try:
            section = request.form['section']
        except HTTPException:
            section = session['section']

        db = DatabaseController()
        error = None

        if not name:
            error = 'Username is required.'
        if not last_name:
            error = 'Password is required.'
        if not nickname:
            nickname = '-'
        if not oib:
            error = 'Oib value is required.'
        if not phone_number:
            error = 'Phone number is required.'
        if not date_of_birth:
            error = 'Date of birth is required.'
        if not membership_start:
            error = 'Membership start date is required.'
        if not card_id:
            error = 'Card id is required.'
        if not email:
            error = 'Email is required.'
        if not section or section == 'Izaberi sekciju':
            error = 'Sekcija value is required.'
        if db.member_exists(card_id.strip()):
            registered_member = db.get_row(DatabaseTables.CLAN, 'broj_iskaznice', card_id.strip())
            name, last_name = registered_member[1], registered_member[2]
            error = 'Broj iskaznice već postoji i glasi na ime {0} {1}'.format(name, last_name)

        if db.member_exists_by_name(name, last_name, nickname):
            error = 'Član %s %s nadimka %s već postoji! Promijeni nadimak za uspješno dodavanje člana.' % \
                    (name, last_name, nickname)

        if error is None:
            date_of_birth = get_date_object(date_of_birth)
            membership_start = get_date_object(membership_start)
            entry_values = (name, last_name, nickname, oib, phone_number, date_of_birth, membership_start,
                            card_id, email)
            db.add_member_entry(entry_values)

            db.add_member_card((db.get_member_id(name, last_name, nickname), Iskaznice.PLAVA, membership_start))

            member_id = db.get_member_id(name, last_name, nickname)
            native_section = 1  # Sekcija novododanog člana je matična
            db.add_member_to_section((member_id, section, membership_start, native_section))

            flash("Član %s %s je uspješno dodan!" % (name, last_name), 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('/members/add.html')


@members_bp.route('/list', methods=['GET'])
@login_required
def list_members():
    db = DatabaseController()
    if session["access_level"] >= AccessLevels.SAVJETNIK:
        members = [x[:-3] for x in db.get_all_members()]
    else:
        members = [x[:-1] for x in db.get_all_members_admin()]

    members_list = {}
    for member in members:
        if db.is_member_active(member[0]):
            members_list[member[0]] = member[1:] + (db.get_member_primary_section(member[0]), ) \
                                      + (Utilities.card_colors[db.get_member_card_color(member[0])], )

    if session["access_level"] >= AccessLevels.SAVJETNIK:
        sorted_list = sorted(members_list.items(), key=lambda x: x[1][1])  # Sort po prezimenu ako je unutar sekcije
    else:
        sorted_list = sorted(members_list.items(), key=lambda x: (x[1][-2], x[1][1]))  # Sort po sekciji prvo pa prezimenu

    sorted_members = {}
    for k, v in sorted_list:
        sorted_members[k] = v

    return render_template("/members/list.html", list_records=sorted_members)


@members_bp.route('/edit/<member_id>', methods=['GET', 'POST'])
@login_required
@savjetnik_required
def edit_member(member_id):
    db = DatabaseController()
    member = db.get_row(DatabaseTables.CLAN, 'id', member_id)
    member_section = db.get_member_primary_section(member_id)
    member_card = db.get_member_card_color(member_id)
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['lastname']
        nickname = request.form['nickname']
        oib = request.form['oib']
        phone_number = request.form['phone']
        date_of_birth = request.form['dateofbirth']
        membership_start = request.form['membership']
        card_id = request.form['idcard']
        email = request.form['email']

        section_change = False
        card_color_change = False
        try:
            section = request.form['section']
            if section != member_section:
                section_change = True
        except HTTPException:
            section = member_section

        try:
            card_color = request.form['cardcolor']
            if card_color != member_card:
                card_color_change = True
        except HTTPException:
            card_color = member_card

        db = DatabaseController()
        error = None

        if not name:
            error = 'Username is required.'
        if not last_name:
            error = 'Password is required.'
        if not nickname:
            nickname = '-'
        if not oib:
            error = 'Oib value is required.'
        if not phone_number:
            error = 'Phone number is required.'
        if not date_of_birth:
            error = 'Date of birth is required.'
        if not membership_start:
            error = 'Membership start date is required.'
        if not card_id:
            error = 'Card id is required.'
        if not email:
            error = 'Email is required.'
        if not section or section == 'Izaberi sekciju':
            error = 'Sekcija value is required.'
        if card_id != member[8] and db.member_exists(card_id.strip()):
            registered_member = db.get_row(DatabaseTables.CLAN, 'broj_iskaznice', card_id.strip())
            name, last_name = registered_member[1], registered_member[2]
            error = 'Broj iskaznice već postoji i glasi na ime {0} {1}'.format(name, last_name)

        if error is None:
            date_of_birth = get_date_object(date_of_birth)
            membership_start = get_date_object(membership_start)
            entry_values = (name, last_name, nickname, oib, phone_number, date_of_birth, membership_start,
                            card_id, email)
            db.edit_member(member_id, entry_values)

            if section_change:
                if member_already_joined(member_id, section):
                    db.change_member_section_to_primary(member_id, section)
                else:
                    db.edit_member_section((member_id, section, datetime.date.today()))

            if card_color_change:
                today_date = datetime.date.today()
                if not db.member_has_card_color(member_id, card_color):
                    db.add_member_card((member_id, card_color, today_date))
                else:
                    db.edit_member_card((today_date, member_id, card_color))

            flash("Podaci člana %s %s je uspješno izmjenjen!" % (name, last_name), 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('/members/edit.html', member=member[1:-2], member_section=member_section,
                           member_id=member[0], sections=Utilities.sections, member_card=member_card,
                           cards=Utilities.card_colors)


@members_bp.route('/remove/<member_id>', methods=['POST'])
@savjetnik_required
@login_required
def remove_member(member_id):

    if request.method == 'POST':

        db = DatabaseController()
        if not db.entry_exists(DatabaseTables.CLAN, member_id):
            error = 'Neuspješno arhiviranje. Zapis ne postoji u bazi.'
            flash(error, 'danger')
        else:
            db.deactivate_member(member_id)
            flash('Član uspješno arhiviran', 'success')

    return "1"


@members_bp.route('/erase/<member_id>', methods=['POST'])
@admin_required
@login_required
def erase_member(member_id):

    if request.method == 'POST':

        db = DatabaseController()
        if not db.entry_exists(DatabaseTables.CLAN, member_id):
            error = 'Neuspješno brisanje. Zapis ne postoji u bazi.'
            flash(error, 'danger')
        else:
            db.remove_entry(DatabaseTables.CLAN, member_id)
            flash('Član uspješno izbrisan', 'success')

    return "1"


@members_bp.route('/archive', methods=['GET'])
@login_required
def archive():
    db = DatabaseController()
    all_archived_members = db.get_row(DatabaseTables.CLAN, 'aktivan', 0, return_all=True)
    members_list = {}
    for member in sorted(all_archived_members, key=lambda x: x[10]):
        members_list[member[0]] = (member[1], member[2], member[3], member[7],
                                   member[8], member[9], db.get_member_primary_section(member[0]), member[-1])

    return render_template('/members/archive.html', members_list=members_list)


@members_bp.route('/<member_id>/activate', methods=['POST'])
@login_required
@savjetnik_required
def activate(member_id=None):
    if request.method == 'POST':
        db = DatabaseController()
        db.activate_member(member_id)
        flash('Član je uspješno aktiviran', 'success')

    return "1"


@members_bp.route('/associate', methods=['GET', 'POST'])
@login_required
@savjetnik_required
def associate():
    db = DatabaseController()
    member = ['-'] * 10
    member_section = '-'
    sections = Utilities.sections_and_teams
    if request.method == 'POST':
        card_id = request.form['idcard']
        if request.form['action'] == 'search':
            if db.member_exists(card_id):
                member_id = db.get_member_by_card_id(card_id)[0]
                member = db.get_table_row(DatabaseTables.CLAN, member_id)
                if member_already_joined(member_id, session['section']):
                    flash("Član %s %s je već učlanjen u %s sekciju" % (member[1], member[2], session['section']), "info")
                else:
                    member = db.get_table_row(DatabaseTables.CLAN, member_id)
                    member_section = db.get_member_primary_section(member_id)
                    sections = get_available_sections_to_join(member_id)
            else:
                flash("Ne postoji član sa tim brojem članske iskaznice", "danger")
        else:
            error = None
            if db.member_exists(card_id):
                member_id = db.get_member_by_card_id(card_id)[0]
                member = db.get_table_row(DatabaseTables.CLAN, member_id)
                name = request.form['name']
                last_name = request.form.get('lastname')
                nickname = request.form.get('nickname')
                section = None
                print(db.get_member_card_id(name, last_name, nickname))
                if card_id != db.get_member_card_id(name, last_name, nickname):
                    error = "Broj iskaznice nije jednak broju iskaznice od nađenog člana. " \
                            "Nakon mijenjanja broja iskaznice je potrebno pritisnuti gumb Traži."

                try:
                    section = request.form['section']
                except HTTPException:
                    error = "Izaberi sekciju prije potvrđivanja pridruživanja"

                if error is None:
                    membership_start = datetime.datetime.today()
                    native_section = 0
                    db.add_member_to_section((member_id, section, membership_start, native_section))

                    flash("Člana %s %s je uspješno pridružen %s sekciji!" % (name, last_name, section), 'success')
                    return redirect(url_for('index'))
            else:
                error = "Ne postoji član sa tim brojem članske iskaznice"
            flash(error, 'danger')

    return render_template('/members/associate.html', member=member[1:-2], member_section=member_section,
                           member_id=member[0], sections=sections)


def get_available_sections_to_join(member_id):
    db = DatabaseController()
    joined_sections = [x for x in db.get_all_members_sections(member_id)]
    return {x: v for x, v in Utilities.sections_and_teams.items() if x not in joined_sections}


def member_already_joined(member_id, section_name):
    db = DatabaseController()
    possible_sections = [x for x in db.get_all_members_sections(member_id)]
    for section in possible_sections:
        if section == section_name:
            return True
    return False

