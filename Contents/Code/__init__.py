DEBUG = True

PREFIX = '/video/fulhamfc'
NAME = L('Title')

'''
FFC_DOT_COM = 'http://www.fulhamfc.com'
'''

ART = R('art-default.jpg')
ICON = R('icon-default.png')

YT_PLAYLIST_URL = 'https://gdata.youtube.com/feeds/api/playlists/%s?v=2&alt=json&start-index=%d&max-results=%d'

YT_PLAYLISTS = {'goals': {'playlist': 'PLY8T1xH7hxopNeqTcMIGCMAKTI3fMfFEt', 'title': 'Goals'},
                'highlights': {'playlist': 'PLY8T1xH7hxorsg8f9l3Xe3Kkc3NKmfH7t', 'title': 'Highlights'},
                'reaction': {'playlist': 'PLY8T1xH7hxooe9bWd8UEdR4eajC5X1zkc', 'title': 'Reaction'},
                'previews': {'playlist': 'PLY8T1xH7hxooyNHwI90VSBR6uPO-NxdkX', 'title': 'Previews'},
                'features': {'playlist': 'PLY8T1xH7hxopsP7OE1MskMCtUYV9g6vVU', 'title': 'Features'},
                'u18': {'playlist': 'PLY8T1xH7hxoqin2v-iCgFV0rj-3kq1sUa', 'title': 'U18'},
                'u21': {'playlist': 'PLY8T1xH7hxoodbUB6g86QE89N1kpQK2xT', 'title': 'U21'},
                'flashbacks': {'playlist': 'PLY8T1xH7hxoon4TrZA3JFckiuWFnwoMa9', 'title': 'Flashbacks'}}

MAXRESULTS = 20


####################################################################################################
def Start():

    Plugin.AddViewGroup("InfoList", viewMode="InfoList")
    Plugin.AddViewGroup("List", viewMode="List")

    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = NAME
    ObjectContainer.art = ART
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = ICON
    VideoClipObject.thumb = ICON

    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36"


####################################################################################################
@handler(PREFIX, L('VideoTitle'))
def MainMenu():

    oc = ObjectContainer()

    #oc.add(DirectoryObject(key=Callback(DailyLift), title="Daily Lift", thumb=R('daily-lift.jpg')))
    for item in YT_PLAYLISTS:
        #thumb = R(item + '.jpg')
        oc.add(DirectoryObject(key=Callback(YoutubePlaylist, which=item),
                               title=YT_PLAYLISTS[item]['title'],
                               thumb=ICON))

    #oc.add(DirectoryObject(key=Callback(Services), title="Church Services", thumb=SERVICE_ICON))
    #oc.add(DirectoryObject(key=Callback(Thinkers), title="Time4Thinkers", thumb=R(ICON)))

    return oc


####################################################################################################
@route(PREFIX + '/daily-lift')
def DailyLift(page=1):

    page = int(page)
    oc = ObjectContainer(view_group="InfoList", title1="Daily Lift")

    url = DAILY_LIFT_URL
    if page > 1:
        url += '/(offset)/%d' % ((page - 1) * 10)

    html = HTML.ElementFromURL(url)

    thumbs = html.xpath('//div[@class="cover-image"]/img/@src')
    titles = html.xpath('//h2[@class="line-title"]/a')
    byline = html.xpath('//span[contains(@class,"author")]')

    num_thumbs = len(thumbs)
    num_titles = len(titles)
    log("Thumbs: %d, Titles: %d, Bylines: %d" % (num_thumbs, num_titles, len(byline)))

    if num_thumbs < 1 or num_titles < 1 or num_thumbs != num_titles:
        return ObjectContainer(header=NAME, message="There was a problem retrieving the Daily Lifts.")

    for index in range(num_thumbs):
        url = FFC_DOT_COM + titles[index].get('href')
        title = titles[index].text
        summary = ' '.join(byline[index].xpath('.//text()')).split('.')[0]
        thumb = FFC_DOT_COM + thumbs[index]

        oc.add(TrackObject(url=url, summary=summary, thumb=thumb, title=title, duration=120000))

    oc.add(NextPageObject(key=Callback(DailyLift, page=page + 1), title="More Lifts..."))

    return oc


####################################################################################################
@route(PREFIX + '/services')
def Services():

    oc = ObjectContainer(view_group="InfoList", title1="Church Services")

    oc.add(TrackObject(url=SUNDAY_URL, title="Sunday Service", thumb=SERVICE_ICON))
    oc.add(TrackObject(url=WEDNESDAY_URL, title="Wednesday Meeting", thumb=SERVICE_ICON))
    #oc.add(TrackObject(url=THANKSGIVING_URL, title="Thanksgiving Service", thumb=SERVICE_ICON))

    return oc


####################################################################################################
# mostly pulled from https://github.com/shopgirl284/Webisodes.bundle/blob/master/Contents/Code/__init__.py
@route(PREFIX + '/youtube-playlist')
def YoutubePlaylist(which='highlights', page=1):

    page_title = YT_PLAYLISTS[which]['title']
    playlist = YT_PLAYLISTS[which]['playlist']

    page = int(page)
    start = (page - 1) * MAXRESULTS + 1

    json_url = YT_PLAYLIST_URL % (playlist, start, MAXRESULTS)

    data = JSON.ObjectFromURL(json_url)

    oc = ObjectContainer(title1=page_title, replace_parent=(page > 1))

    if 'entry' in data['feed']:
        for video in data['feed']['entry']:

            # Determine the actual HTML URL associated with the view. This will allow us to simply redirect
            # to the associated URL Service, when attempting to play the content.
            video_url = None
            for video_links in video['link']:
                if video_links['type'] == 'text/html':
                    video_url = video_links['href']
                    break

            # This is very unlikely to occur, but we should at least log.
            if video_url is None:
                Log('Found video that had no URL')
                continue

            video_title = video['media$group']['media$title']['$t']

            if 'media$thumbnail' in video['media$group']:
                thumb = video['media$group']['media$thumbnail'][0]['url']
            else:
                thumb = ICON

            duration = None
            try:
                duration = int(video['media$group']['yt$duration']['seconds']) * 1000
            except:
                pass

            summary = None
            try:
                summary = video['media$group']['media$description']['$t']
            except:
                pass

            # [Optional]
            date = None
            try:
                date = Datetime.ParseDate(video['published']['$t'].split('T')[0])
            except:
                try:
                    date = Datetime.ParseDate(video['updated']['$t'].split('T')[0])
                except:
                    pass

            oc.add(VideoClipObject(
                url=video_url,
                title=video_title,
                summary=summary,
                thumb=thumb,
                originally_available_at=date,
                duration=duration
            ))

    oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)

    # Check to see if there are any further results available.
    if data['feed'].has_key('openSearch$totalResults'):
        total_results = int(data['feed']['openSearch$totalResults']['$t'])
        items_per_page = int(data['feed']['openSearch$itemsPerPage']['$t'])
        start_index = int(data['feed']['openSearch$startIndex']['$t'])

        if (start_index + items_per_page) < total_results:
            oc.add(NextPageObject(key=Callback(YoutubePlaylist, which=which, page=page + 1), title="More Videos..."))

    return oc


####################################################################################################
def log(str):
    if DEBUG:
        Log.Debug(str)