import sqlite3, os
from apiclient.discovery import build
from flask import Flask, request, session, g, redirect, \
     url_for, render_template
from youtube.ner import entity
from operator import itemgetter

directory = os.path.dirname(os.path.realpath(__file__))

# configuration
DATABASE = directory + '/youtube.db'
DEVELOPER_KEY = "AIzaSyBdLy0yxLKo-Az9oDY4RTb2-IjllcBtgQY"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def front_page():
    return render_template('front.html')

# Front page of YouTube music trend
#View function of trend.html
#variables on the template:
#entries - artist[] - rank
#                   - artist_name
#                   - trend   
#        - track[] - rank
#                  - track_name
#                  - trend 
#                  - video_id
@app.route('/trend')
def show_trend():
    entries = dict(artist=[], track=[])
    cur1 = g.db.execute('''SELECT artist, trend 
                           FROM artist_trend
                           WHERE artist NOT NULL
                           ORDER BY trend DESC
                           LIMIT 100''')
    cur2 = g.db.execute('''SELECT artist, song, trend, id
                           FROM track_trend
                           WHERE artist NOT NULL
                           AND song NOT NULL
                           ORDER BY trend DESC
                           Limit 170''')
    sql_result = cur2.fetchall()
    cur_dict, tt= combine_name(input_list=sql_result, key_field=3,
                               max_field=2,
                               combine_fields=(0,1),
                               attach_fields=(),
                               avoid_keys=[]) 
                                                                             
    entries['artist'] = [dict(artist_name = item[0],
                              trend = '{:,}'.format(item[1])) \
                         for i, item in enumerate(cur1.fetchall())]
    entries['track'] = [dict(artist_set = cur_dict[key][1][0],
                             song_set = cur_dict[key][1][1],
                             trend = '{:,}'.format(cur_dict[key][0]),
                             trend_num = cur_dict[key][0],
                             video_id = key) \
                        for key in cur_dict][:100]
    entries['track'].sort(key=itemgetter('trend_num'), reverse=True) 
    return render_template('trend.html', entries=entries)
    
    
#YouTube search function
#View function of search.html
#URL variables:
#    - query_type: 'youtube' or 'artist'
#    - query: artist name or inputed query from
#             youtube search bar
#Variables on the template:
#entries - query_type
#        - search_list[] - video_id
#                        - title
#                        - (trend)
@app.route('/search/<query_type>/<query>/<int:count>')
def search(query_type, query, count):
    entries = dict(query_type=query_type, 
                   search_list=[])
    if query_type == 'youtube':
        youtube = build(YOUTUBE_API_SERVICE_NAME, 
                        YOUTUBE_API_VERSION,
                        developerKey=DEVELOPER_KEY)
        query = request.args.get('query')
        #entries['query'] = query
        search_response = youtube.search().list(
          q=query,
          type='video',
          videoCategoryId='10',
          part="id,snippet",
          maxResults=count,
          ).execute()
        for result in search_response.get('items', []):
            video_id = result['id']['videoId']
            video_title = result['snippet']['title']
            entries['search_list'].append(dict(video_id = video_id, 
                                            title = video_title))
    elif query_type == 'artist':
        cur = g.db.execute('''SELECT song, trend, id
                              FROM track_trend
                              WHERE artist = ?
                              AND song NOT NULL
                              ORDER BY trend DESC
                              LIMIT ?''', (query, count))   
        sql_result = cur.fetchall()
        cur_dict,tt = combine_name(input_list=sql_result, key_field=2,
                                   max_field=1,
                                   combine_fields=(0,),
                                   attach_fields=(),
                                   avoid_keys=[]) 
        entries['search_list'] = [dict(video_id=key,
                                       artist = query,
                                       song = ' | '.join(cur_dict[key][1][0]),
                                       trend = '{:,}'.format(cur_dict[key][0]),
                                       trend_num = cur_dict[key][0])
                                  for key in cur_dict]
        entries['search_list'].sort(key=itemgetter('trend_num'), reverse=True)
    elif query_type == 'song':
        cur = g.db.execute('''SELECT artist, trend, id
                              FROM track_trend
                              WHERE song = ?
                              AND artist NOT NULL
                              ORDER BY trend DESC
                              LIMIT ?''', (query, count))
        sql_result = cur.fetchall()
        cur_dict, tt = combine_name(input_list=sql_result, key_field=2,
                                    max_field=1,
                                    combine_fields=(0,),
                                    attach_fields=(),
                                    avoid_keys=[]) 
        entries['search_list'] = [dict(video_id=key,
                                       artist = ' | '.join(cur_dict[key][1][0]),
                                       song = query,
                                       trend = '{:,}'.format(cur_dict[key][0]),
                                       trend_num = cur_dict[key][0])
                                  for key in cur_dict]        
        entries['search_list'].sort(key=itemgetter('trend_num'), reverse=True)
    return render_template('search.html', entries=entries)
        
    

#Listen to YouTube video
#view function for watch.html
#URL variables:
#    -video_id: youtube video id
#variables on the template:
#entries - video_id
#        - artist[] - song_name
#                   - trend
#                   - video_id
#        - song[] - artist_name
#                 - trend
#                 - video_id
@app.route('/watch/<video_id>')
def watch(video_id):
    entries = {}
    entries['video_id'] = video_id
    entries['artist'] = set()
    entries['song'] = set()
    entries['trend'] = 'unknown'
    entries['cat'] = 'music'
    cur = g.db.execute('''SELECT id, click, artist, song, title
                          FROM meta
                          WHERE id = ?''', (video_id,))
    records = cur.fetchall()
    if records:
        for item in records:
            entries['artist'].add(item[2]) 
            entries['song'].add(item[3]) 
        entries['title'] = item[4]
    else:
        youtube = build(YOUTUBE_API_SERVICE_NAME, 
                        YOUTUBE_API_VERSION,
                        developerKey=DEVELOPER_KEY)
        response = youtube.videos().list(
          id=video_id,
          part='snippet',
          ).execute()   
        items = response.get('items', [])
        if len(items) == 1:
            result = items[0] 
            entries['title'] = result['snippet'].get('title', '')
            temp = entity(entries['title'], source='raw', check=True)
            if temp == 'no music':
                entries['cat'] = temp
                return render_template('watch.html', entries=entries)
            entries['artist'] = temp['ARTIST']
            entries['song'] = temp['SONG']
            
    artist = {}
    song = {}
    for name in entries['artist']:
        cur = g.db.execute('''SELECT song, trend, id
                              FROM track_trend
                              WHERE artist = ?
                              AND song NOT NULL
                              ORDER BY trend DESC
                              LIMIT 25''',
                              (name,))
        sql_result = cur.fetchall()
        cur_dict, v_trend = combine_name(input_list=sql_result, key_field=2,
                                         max_field=1,
                                         combine_fields=(0,),
                                         attach_fields=(),
                                         avoid_keys=[video_id])
        artist[name] = [dict(song_name = ' | '.join(cur_dict[key][1][0]), 
                             trend_num = cur_dict[key][0],
                             trend = '{:,}'.format(cur_dict[key][0]),
                             video_id = key)
                        for key in cur_dict]
        artist[name].sort(key=itemgetter('trend_num'), reverse=True)
        if v_trend != 'unknown':
            entries['trend'] = '{:,}'.format(v_trend)
                        
    for name in entries['song']:
        cur = g.db.execute('''SELECT artist, trend, id
                              FROM track_trend
                              WHERE song = ?
                              AND artist NOT NULL
                              ORDER BY trend DESC
                              LIMIT 25''',
                              (name,))
        sql_result = cur.fetchall()
        cur_dict, v_trend = combine_name(input_list=sql_result, key_field=2,
                                         max_field=1,
                                         combine_fields=(0,), 
                                         attach_fields=(),
                                         avoid_keys=[video_id])             
        song[name] = [dict(artist_name = ' | '.join(cur_dict[key][1][0]),
                           trend_num = cur_dict[key][0],
                           trend = '{:,}'.format(cur_dict[key][0]),
                           video_id = key)
                      for key in cur_dict]
        song[name].sort(key=itemgetter('trend_num'), reverse=True)
        if v_trend != 'unknown':
            entries['trend'] = '{:,}'.format(v_trend)
        
    entries['artist'] = artist
    entries['song'] = song    
    entries['artist'].pop(None, None) 
    entries['song'].pop(None, None) 
    return render_template('watch.html', entries=entries)


#aggregate replicates from sql query results 
def combine_name(input_list, key_field, max_field, combine_fields,
                 attach_fields, avoid_keys):
    cur_dict = {}
    trend = 'unknown'
    for item in input_list:
        key = item[key_field]
        if key in avoid_keys:
            trend = item[max_field]
            continue
        i_max = -float('inf')
        i_combine = [set() for i in combine_fields]
        cur_value = cur_dict.get(key, [i_max, i_combine, None])
        cur_max = max(item[max_field], cur_value[0])
        cur_value[0] = cur_max
        for i, ind in enumerate(combine_fields):
            cur_value[1][i].add(item[ind])
        if cur_value[2] == None:
            cur_value[2] = [item[i] for i in attach_fields]
        cur_dict[key] = cur_value
    return cur_dict, trend
        
    
@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])
    
    
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()    



    
if __name__ == '__main__':
    app.run(debug=True)
        
