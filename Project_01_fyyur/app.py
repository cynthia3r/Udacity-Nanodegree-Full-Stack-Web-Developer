# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request, Response,
    flash,
    redirect,
    url_for, jsonify
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy import func

import sys
# Import database URI from config file
from config import SQLALCHEMY_DATABASE_URI
# Import package for db migration scripts
from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# Create instance of Migrate for Database schema migration
migrate = Migrate(app, db)

# TODO COMPLETED: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

# TODO COMPLETED: Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
Show = db.Table('Show',
                db.Column('venue_id', db.Integer, db.ForeignKey(
                    'Venue.id'), nullable=False),
                db.Column('artist_id', db.Integer, db.ForeignKey(
                    'Artist.id'), nullable=False),
                db.Column('start_time', db.DateTime, nullable=False),
                )


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO COMPLETED: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship('Artist', secondary=Show,
                              backref=db.backref('venues', lazy=True))

    def __repr__(self):
        return f'<Venue ID : {self.id}, Venue name: {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    # Changed datatype of genres to db.Array as it can hold multiple values for genres
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO COMPLETED: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))

    def __repr__(self):
        return f'<Artist ID : {self.id}, Artist name: {self.name}>'
# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    # Challenge COMPLETED: Return results for recently listed Artists and Venues sorted by newly created
    # Limit to the 10 most recently listed items
    recent_listed_artists = Artist.query.order_by(
        Artist.id.desc()).limit(10).all()
    recent_listed_venues = Venue.query.order_by(
        Venue.id.desc()).limit(10).all()
    return render_template('pages/home.html',
                        recent_listed_artists=recent_listed_artists,
                        recent_listed_venues=recent_listed_venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO COMPLETED: replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    venues_in_state_city = db.session.query(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state)

    for venue_regions in venues_in_state_city:
        venue_records = db.session.query(Venue).filter_by(
            city=venue_regions[0]).filter_by(state=venue_regions[1]).all()
        venue_result = []
        for venue in venue_records:
            venue_result.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": db.session.query(func.count(Show.c.venue_id)).filter(Show.c.venue_id == venue.id).filter(Show.c.start_time > datetime.now()).all()[0][0]
            })

        data.append({
            "city": venue_regions[0],
            "state": venue_regions[1],
            "venues": venue_result
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO COMPLETED: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    results = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()

    data = []

    for result in results:
        num = db.session.query(func.count(Show.c.venue_id)).filter(
            Show.c.venue_id == result.id).filter(Show.c.start_time > datetime.now()).all()[0][0]
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": db.session.query(func.count(Show.c.venue_id)).filter(Show.c.venue_id == result.id).filter(Show.c.start_time > datetime.now()).all()[0][0]
        })

    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO COMPLETED: replace with real venue data from the venues table, using venue_id

    venue = Venue.query.get(venue_id)
    past_shows_result = db.session.query(Show).filter(
        Show.c.venue_id == venue.id).filter(Show.c.start_time <= datetime.now()).all()
    past_shows = []
    upcoming_shows_result = db.session.query(Show).filter(
        Show.c.venue_id == venue.id).filter(Show.c.start_time > datetime.now()).all()
    upcoming_shows = []

    for show in past_shows_result:
        artist_name = db.session.query(Artist.name).filter(
            Artist.id == show.artist_id)[0][0]
        artist_image_link = db.session.query(Artist.image_link).filter(
            Artist.id == show.artist_id)[0][0]
        past_shows.append({
            "artist_id": show.artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    for show in upcoming_shows_result:
        artist_name = db.session.query(Artist.name).filter(
            Artist.id == show.artist_id)[0][0]
        artist_image_link = db.session.query(Artist.image_link).filter(
            Artist.id == show.artist_id)[0][0]
        upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO COMPLETED: insert form data as a new Venue record in the db, instead
    # TODO COMPLETED: modify data to be the data object returned from db insertion
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        image_link = request.form['image_link']
        website = request.form['website']
        seeking_talent = True if 'seeking_talent' in request.form else False
        seeking_description = request.form['seeking_description']
        venue = Venue(name=name,
                city=city,
                state=state,
                address=address,
                phone=phone,
                genres=genres,
                facebook_link=facebook_link,
                image_link=image_link,
                website=website,
                seeking_talent=seeking_talent,
                seeking_description=seeking_description)
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + venue.name + ' was successfully listed!')
    except:
        # TODO COMPLETED: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO COMPLETED: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ID ' + venue_id + ' was successfully deleted!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ID ' +
              venue_id + ' could not be deleted.')
    finally:
        db.session.close()

    # BONUS CHALLENGE COMPLETED: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO COMPLETED: replace with real data returned from querying the database
    data = db.session.query(Artist).all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO COMPLETED: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    results = db.session.query(Artist).filter(
        Artist.name.ilike(f'%{search_term}%')).all()

    data = []

    for result in results:
        num = db.session.query(func.count(Show.c.artist_id)).filter(
            Show.c.artist_id == result.id).filter(Show.c.start_time > datetime.now()).all()[0][0]
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": db.session.query(func.count(Show.c.artist_id)).filter(Show.c.artist_id == result.id).filter(Show.c.start_time > datetime.now()).all()[0][0]
        })

    response = {
        "count": len(results),
        "data": data,
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash('Artist ID' + artist_id + ' was successfully deleted!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ID ' +
              artist_id + ' could not be deleted.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    artist = Artist.query.get(artist_id)
    past_shows_result = db.session.query(Show).filter(
        Show.c.artist_id == artist.id).filter(Show.c.start_time <= datetime.now()).all()
    past_shows = []
    upcoming_shows_result = db.session.query(Show).filter(
        Show.c.artist_id == artist.id).filter(Show.c.start_time > datetime.now()).all()
    upcoming_shows = []

    for show in past_shows_result:
        venue_name = db.session.query(Venue.name).filter(
            Venue.id == show.venue_id)[0][0]
        venue_image_link = db.session.query(
            Venue.image_link).filter(Venue.id == show.venue_id)[0][0]
        past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "venue_image_link": venue_image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    for show in upcoming_shows_result:
        venue_name = db.session.query(Venue.name).filter(
            Venue.id == show.venue_id)[0][0]
        venue_image_link = db.session.query(
            Venue.image_link).filter(Venue.id == show.venue_id)[0][0]
        upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "venue_image_link": venue_image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    # TODO COMPLETED: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)

    if artist:
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres
        form.facebook_link.data = artist.facebook_link
        form.image_link.data = artist.image_link
        form.website.data = artist.website
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO COMPLETED: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    artist = Artist.query.get(artist_id)

    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.website = request.form['website']
        artist.seeking_venue = True if 'seeking_venue' in request.form else False
        artist.seeking_description = request.form['seeking_description']

        db.session.commit()
        # on successful db update, flash success
        flash('Artist information was successfully updated!')
    except:
        flash('An error occurred. Updation of Artist information failed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO COMPLETED: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)

    if venue:
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.address.data = venue.address
        form.phone.data = venue.phone
        form.genres.data = venue.genres
        form.facebook_link.data = venue.facebook_link
        form.image_link.data = venue.image_link
        form.website.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO COMPLETED: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website = request.form['website']
        venue.seeking_talent = True if 'seeking_talent' in request.form else False
        venue.seeking_description = request.form['seeking_description']

        db.session.commit()
        # on successful db update, flash success
        flash('Venue information was successfully updated!')
    except:
        flash('An error occurred. Updation of Venue information failed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO COMPLETED: insert form data as a new Venue record in the db, instead
    # TODO COMPLETED: modify data to be the data object returned from db insertion
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']

        image_link = request.form['image_link']
        website = request.form['website']
        seeking_venue = True if 'seeking_venue' in request.form else False
        seeking_description = request.form['seeking_description']
        artist = Artist(name=name,
                        city=city,
                        state=state,
                        phone=phone,
                        genres=genres,
                        facebook_link=facebook_link,
                        image_link=image_link,
                        website=website,
                        seeking_venue=seeking_venue,
                        seeking_description=seeking_description)
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + artist.name + ' was successfully listed!')
    except:
        # TODO COMPLETED: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO COMPLETED: replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per venue.

    shows_query_result = db.session.query(Show).join(Venue).join(Artist).all()
    data = []

    for show in shows_query_result:
        venue_name = db.session.query(Venue.name).filter(
            Venue.id == show.venue_id)[0][0]
        artist_name = db.session.query(Artist.name).filter(
            Artist.id == show.artist_id)[0][0]
        artist_image_link = db.session.query(Artist.image_link).filter(
            Artist.id == show.artist_id)[0][0]
        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "artist_id": show.artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO COMPLETED: insert form data as a new Show record in the db, instead
    try:
        venue_id = request.form['venue_id']
        artist_id = request.form['artist_id']
        start_time = request.form['start_time']

        show = Show.insert().values(venue_id=venue_id,
                                    artist_id=artist_id, start_time=start_time)
        db.session.execute(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        # TODO COMPLETED: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
