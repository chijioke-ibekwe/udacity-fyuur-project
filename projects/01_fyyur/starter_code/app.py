#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venue_locations = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  print(venue_locations)
  data = []
  for venue_location in venue_locations:
    venues = Venue.query.filter(Venue.city == venue_location[0], Venue.state == venue_location[1]).all()
    venue_sub_data = []
    for venue in venues:
      now = datetime.now()
      upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > now).all()
      sub_data = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      }
      venue_sub_data.append(sub_data)

    venue_data = {
      "city": venue_location[0],
      "state": venue_location[1],
      "venues": venue_sub_data
    }
    data.append(venue_data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'))
  venues_list = []
  for venue in venues:
    now = datetime.now()
    upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > now).all()
    data = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows)
    }
    venues_list.append(data)

  response={
    "count": venues.count(),
    "data": venues_list
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  now = datetime.now()
  past = db.session.query(Artist).join(Show).filter(Show.venue_id==venue_id).filter(Show.start_time < now).all()
  upcoming = db.session.query(Artist).join(Show).filter(Show.venue_id==venue_id).filter(Show.start_time > now).all()
  upcoming_shows = []
  past_shows = []

  for artist in upcoming:
    for show in artist.venues:
      data = {
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(value=str(show.start_time), format="full")
      }
    upcoming_shows.append(data)

  for artist in past:
    for show in artist.venues:
      data = {
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(value=str(show.start_time), format="full")
      }
    past_shows.append(data)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    form = request.form.to_dict(flat=False)
    print(form)
    genre_string = ''
    genres = form.get('genres')
    seeking_talent = form.get('seeking_talent')[0]

    for genre in genres:
      genre_string = genre_string + genre
      if genres.index(genre) != len(genres) - 1:
        genre_string = genre_string + ','

    if seeking_talent == 'y':
      seeking_talent_bool = True
    else:
      seeking_talent_bool = False

    venue = Venue(name=form.get('name')[0], city=form.get('city')[0], state=form.get('state')[0], address=form.get('address')[0], 
    phone=form.get('phone')[0], image_link=form.get('image_link')[0], genres=genre_string, facebook_link=form.get('facebook_link')[0], 
    website_link=form.get('website_link')[0], seeking_talent=seeking_talent_bool, seeking_description=form.get('seeking_description')[0])

    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    error = True
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
        db.session.close()
  if error:
      abort(400)
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    print(venue)
    db.session.delete(venue)
    db.session.commit()
  except BaseException as e:
    db.session.rollback()
    error = True
    print(e)
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = []
  for artist in artists:
    sub_data = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(sub_data)
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%'))
  artists_list = []
  for artist in artists:
    now = datetime.now()
    upcoming_shows = Show.query.filter(Show.artist_id == artist.id, Show.start_time > now).all()
    data = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows)
    }
    artists_list.append(data)

  response={
    "count": artists.count(),
    "data": artists_list
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  now = datetime.now()
  past = db.session.query(Venue).join(Show).filter(Show.artist_id==artist_id).filter(Show.start_time < now).all()
  upcoming = db.session.query(Venue).join(Show).filter(Show.artist_id==artist_id).filter(Show.start_time > now).all()
  upcoming_shows = []
  past_shows = []

  for venue in past:
    for show in venue.artists:
      data = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": format_datetime(value=str(show.start_time), format="full")
      }
    past_shows.append(data)

  for venue in upcoming:
    for show in venue.artists:
      data = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": format_datetime(value=str(show.start_time), format="full")
      }
    upcoming_shows.append(data)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
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
  artist = Artist.query.get(artist_id)
  artist_data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

# TODO: populate form with fields from artist with ID <artist_id>
  form.name.data = artist_data.get('name')
  form.city.data = artist_data.get('city')
  form.state.data = artist_data.get('state')
  form.phone.data = artist_data.get('phone')
  form.genres.data = artist_data.get('genres')
  form.website_link.data = artist_data.get('website')
  form.facebook_link.data = artist_data.get('facebook_link')
  form.image_link.data = artist_data.get('image_link')
  form.seeking_venue.data = artist_data.get('seeking_venue')
  form.seeking_description.data = artist_data.get('seeking_description')

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
    form = request.form.to_dict(flat=False)
    print(form)
    genre_string = ''
    genres = form.get('genres')
    seeking_venue = form.get('seeking_venue')[0]

    for genre in genres:
      genre_string = genre_string + genre
      if genres.index(genre) != len(genres) - 1:
        genre_string = genre_string + ','

    print(genre_string)
    if seeking_venue == 'y':
      seeking_venue_bool = True
    else:
      seeking_venue_bool = False

    artist = Artist.query.get(artist_id)
    artist.name = form.get('name')[0]
    artist.city = form.get('city')[0]
    artist.state = form.get('state')[0]
    artist.phone = form.get('phone')[0]
    artist.image_link = form.get('image_link')[0]
    artist.genres = genre_string
    artist.facebook_link = form.get('facebook_link')[0]
    artist.website_link = form.get('website_link')[0]
    artist.seeking_venue = seeking_venue_bool
    artist.seeking_description = form.get('seeking_description')[0]

    db.session.commit()
  except BaseException as e:
    db.session.rollback()
    error = True
    print(e)
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venue_data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  form.name.data = venue_data.get('name')
  form.city.data = venue_data.get('city')
  form.state.data = venue_data.get('state')
  form.address.data = venue_data.get('address')
  form.phone.data = venue_data.get('phone')
  form.genres.data = venue_data.get('genres')
  form.website_link.data = venue_data.get('website')
  form.facebook_link.data = venue_data.get('facebook_link')
  form.image_link.data = venue_data.get('image_link')
  form.seeking_talent.data = venue_data.get('seeking_talent')
  form.seeking_description.data = venue_data.get('seeking_description')
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
    form = request.form.to_dict(flat=False)
    print(form)
    genre_string = ''
    genres = form.get('genres')
    seeking_talent = form.get('seeking_talent')[0]

    for genre in genres:
      genre_string = genre_string + genre
      if genres.index(genre) != len(genres) - 1:
        genre_string = genre_string + ','

    print(genre_string)
    if seeking_talent == 'y':
      seeking_talent_bool = True
    else:
      seeking_talent_bool = False

    venue = Venue.query.get(venue_id)
    venue.name = form.get('name')[0]
    venue.city = form.get('city')[0]
    venue.state = form.get('state')[0]
    venue.address = form.get('address')[0]
    venue.phone = form.get('phone')[0]
    venue.image_link = form.get('image_link')[0]
    venue.genres = genre_string
    venue.facebook_link = form.get('facebook_link')[0]
    venue.website_link = form.get('website_link')[0]
    venue.seeking_talent = seeking_talent_bool
    venue.seeking_description = form.get('seeking_description')[0]

    db.session.commit()
  except BaseException as e:
    db.session.rollback()
    error = True
    print(e)
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    form = request.form.to_dict(flat=False)
    print(form)
    genre_string = ''
    genres = form.get('genres')
    seeking_venue = form.get('seeking_venue')[0]

    for genre in genres:
      genre_string = genre_string + genre
      if genres.index(genre) != len(genres) - 1:
        genre_string = genre_string + ','

    if seeking_venue == 'y':
      seeking_venue_bool = True
    else:
      seeking_venue_bool = False

    artist = Artist(name=form.get('name')[0], city=form.get('city')[0], state=form.get('state')[0], phone=form.get('phone')[0], 
    genres=genre_string, image_link=form.get('image_link')[0], facebook_link=form.get('facebook_link')[0], 
    website_link=form.get('website_link')[0], seeking_venue=seeking_venue_bool, seeking_description=form.get('seeking_description')[0])

    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    error = True
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
        db.session.close()
  if error:
      abort(400)
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []
  for show in shows:

    venue = show.venue
    artist = show.artist
    sub_data = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.start_time)
    }
    data.append(sub_data)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    form = request.form.to_dict(flat=False)
    print(form)
    show = Show(artist_id=form.get('artist_id')[0], venue_id=form.get('venue_id')[0], start_time=form.get('start_time')[0])
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except BaseException as e:
    print(e)
    db.session.rollback()
    error = True
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
