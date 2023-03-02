import requests
import spotipy
import spotipy.oauth2 as oauth2
from PIL import Image

urls = {}

client_id = "CLIENT_ID"
client_secret = "CLIENT_SECRET"

auth = oauth2.SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
)
sp = spotipy.Spotify(auth.get_access_token())


# info should be str containing artist album
def get_artwork(info):
    print("Attempting Art Retreival for: " + info)
    # takes second result first only because my initial test was Houses of The Holy. Funny enough the song Houses of
    # the holy returns first and is actually on Physical Graffiti, not the album Houses of the Holy

    if "houses of the holy" not in info.lower():
        img = sp.search(info)['tracks']['items'][0]['album']['images'][0]['url']
    else:
        img = sp.search(info)['tracks']['items'][1]['album']['images'][0]['url']

    # open img url and download image
    response = requests.get(img)

    # save image as file
    file = open("images/" + info.replace(" ", "-").replace("\n", "") + ".jpg", "wb")
    file.write(response.content)
    file.close()


def get_vinyls():
    # Open album list and iterate through
    f = open("AlbumList.txt")
    l = []
    while True:
        line = f.readline()
        # break loop when done so we don't try stupid shiz
        if not line:
            break
        # get art for every song and add it to list when exists
        get_artwork(line)
        l.append(line.replace(" ", "-").replace("\n", ""))
    f.close()
    return l


def get_albums(playlists):
    global urls
    if type(playlists) is not list:
        print("Invalid playlist list")
        return

    for playlist in playlists:
        # make sure we have good format
        if type(playlist) is not str:
            continue
        # load playlist and tracks
        results = sp.playlist(playlist)
        tracks = results['tracks']['items']
        results = results['tracks']

        # load all pages ignore error when playlist is too small and results['next'] doesn't exist
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        print("Len of playlist: " + str(len(tracks)))
        count = 0
        # Go through tracks and add image urls to dictionary
        for track in tracks:
            count += 1
            #print(count)
            if track['is_local'] is True:
                continue
            if len(track['track']['album']['images']) == 0:
                continue
            img = track['track']['album']['images'][0]['url']

            if img not in urls:
                urls[track['track']['album']['name']] = img
                #print(track['track']['album']['images'][0]['url'])

        print("image list length: " + str(len(urls)))
    downloadImages()
    return urls

#
def downloadImages():
    global urls
    # Iterate through urls and download each one to images
    for url in urls:
        # open img url and download image
        response = requests.get(urls[url])

        # save image as file
        file = open("largeimages/" + url.replace(" ", "-").replace("/", "-") + ".jpg", "wb")
        file.write(response.content)
        file.close()

        # Resize images so the final composited image isn't insanely large
        # img = Image.open("largeimages/" + url.replace(" ", "-").replace("/", "-") + ".jpg").convert("RGB")
        # img = img.resize((100, 100), Image.ANTIALIAS)
        # img.save("nimages/" + url.replace(" ", "-").replace("/", "-") + ".jpg", "JPEG")


