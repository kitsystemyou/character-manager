from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, jsonify
)
from werkzeug.exceptions import abort

from . import model, db
from sqlalchemy import desc, and_
from datetime import datetime
from flaskr.auth import login_required
from flaskr.model import CharacterSchema, Characters, CocMetaInfo, CocMetaInfoSchema, DynamicSchema
from flask_marshmallow import Marshmallow

bp = Blueprint('character', __name__)


@bp.route('/')
def index():
    characters = Characters.query.order_by(desc(model.Characters.id))
    return render_template('character/index.html', characters=characters)


@bp.route('/character/<int:ch_id>')
def get_character(ch_id):
    character = Characters.query.filter_by(id=ch_id).first()
    print(character)
    # DB 取得結果が配列の場合は最後に.data にする {'status': 'ok', 'hoge': Table_name(... .dump(chara)).data}
    return jsonify({'status': 'ok', 'character': CharacterSchema(many=False).dump(character)})


@bp.route('/character_info/<int:ch_id>')
def get_characters(ch_id):
    print(ch_id)
    character_info = db.session.query(Characters, CocMetaInfo).join(
        CocMetaInfo, Characters.id == CocMetaInfo.character_id).filter(Characters.id == ch_id).first()
    # data = {Characters.__tablename__: character_info[0],
    #         CocMetaInfo.__tablename__: character_info[1]}
    print(type(character_info[0].coc_meta_info))
    print(vars(character_info[0]))

    # dynamic_schema = DynamicSchema(many=False)
    c = CharacterSchema(many=False).dump(character_info[0])
    c['coc_meta_info'] = CocMetaInfoSchema(many=False).dump(character_info[1])
    print(c)
    # return jsonify({'status': 'ok', "result": dynamic_schema.dump(data)})
    return jsonify({'status': 'ok', "result": c})


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        character_name = request.form['character_name']
        player_name = request.form['player_name']
        tags = request.form['tags']
        error = None
        print(session['user_id'])
        if not character_name:
            error = 'character name is required.'

        if error is not None:
            flash(error)
        else:
            character = Characters(
                id=None,
                user_id=session['user_id'],
                character_name=character_name,
                player_name=player_name,
                game_system="CoC",
                prof_img_path="",
                tags=tags,
                create_time=datetime.now(),
                update_time=datetime.now(),
                delete_time=None,
            )
            db.session.add(character)
            db.session.commit()

            return redirect(url_for('character.index'))

    return render_template('character/create.html')


def get_post(id, check_author=True):
    character_info = db.session.query(Characters, CocMetaInfo).join(
        CocMetaInfo, Characters.id == CocMetaInfo.character_id).filter(Characters.id == id).first()

    if character_info is None:
        abort(404, f"Post id {id} doesn't exist.")

    # ログインユーザーの user_id と一致したら返すそれ以外は 403
    # if check_author and character_info.user_id != str(g.user.id):
    #     abort(403)

    return character_info


@ bp.route('/<string:id>/update', methods=('GET', 'POST'))
# @ login_required
def update(id):
    character = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            character.character_name = title
            character.player_name = body
            db.session.commit()
            return redirect(url_for('character.index'))

    return render_template('character/update.html', post=character)
    # return jsonify({'character': entries_schema.dump(character).data})


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    character = Characters.query.filter_by(id=id).first()
    db.session.delete(character)
    db.session.commit()
    return redirect(url_for('character.index'))
