import requests, urllib, unicodedata, os
from mutagen.flac import FLAC

def clear_terminal():
    print("\033[2J\033[10;1H", end='')
    return 0

def cleanup(data):
    for i in range(len(data)):
        if type(data[i])!=int:
            data[i] = data[i].replace("Đ", "Dj").replace("đ", "dj")
            data[i] = unicodedata.normalize('NFKD', data[i]).encode('ascii', 'ignore').decode('ascii')
    return data

def search(query):
    url_get = "https://eu.qobuz.squid.wtf/api/get-music"

    params_get = {
        "q": query,
        "offset": 0
    }

    encoded_params_get = urllib.parse.urlencode(params_get)
    url_get = f"{url_get}?{encoded_params_get}"
    response_get = requests.get(url_get)
    data_get = response_get.json()

    return data_get


def download_track(data):
    nfo_artist = f"""<?xml version="1.0" encoding="UTF-8"?>
<artist>
    <name>{data[0]}</name>
    <sortname>{data[0]}</sortname>
</artist>"""
    nfo_album = f"""<?xml version="1.0" encoding="UTF-8"?>
<album>
    <title>{data[1]}</title>
    <genre></genre>
    <releasedate>{data[2]}</releasedate>
    <albumArtistCredits>
        <artist>{data[0]}</artist>
    </albumArtistCredits>
</album>"""

    data = cleanup(data)

    filepath = f"{music_path}/{data[0]}/{data[1]}"

    if search_type=="track":
        os.makedirs(filepath, exist_ok=True)

        response_cover = requests.get(data[6], stream=True)
    
        with open(f"{filepath}/cover.jpg", 'wb') as f:
            for chunk in response_cover.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    with open(f"{music_path}/{data[0]}/artist.nfo", "w") as f:
        f.write(nfo_artist)
    with open(f"{music_path}/{data[0]}/{data[1]}/album.nfo", "w") as f:
        f.write(nfo_album)

    filename = f"{filepath}/{data[5]:02} - {data[4]}.flac"

    if os.path.isfile(filename):
        print(f"\rDownloaded {data[4]}")
        print()
    else:
        params_down = {
            "track_id": data[3],
            "quality": 27
        }

        url_down = f"{url_down_main}?{urllib.parse.urlencode(params_down)}"

        response_down = requests.get(url_down)
        data_down = response_down.json()
        url = data_down["data"]["url"]
        response = requests.get(url, stream=True)
    
        downloaded = 0
        total_size = int(response.headers.get('Content-Length', 0))

        print(f"Downloading {data[4]}")

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = downloaded * 100 / total_size
                    print(f"\rDownloaded {percent:.2f}%", end='')

    audio = FLAC(filename)
    audio.clear()

    audio["ARTIST"] = data[0]
    audio["ALBUM"] = data[1]
    audio["DATE"] = data[2]
    audio["TITLE"] = data[4]
    audio["TRACKNUMBER"] = str(data[5])

    audio.save()

    print(f"\rDownloaded {data[4]}")
    print()

    return 0

def download_album(data):
    get_tracks = "https://eu.qobuz.squid.wtf/api/get-album?album_id="

    tracklist_down = requests.get(f"{get_tracks}{data[3]}")
    tracklist_data = tracklist_down.json()
    tracklist_ids = tracklist_data["data"]["track_ids"]
    tracklist_info = tracklist_data["data"]["tracks"]["items"]

    cover_url = tracklist_data["data"]["image"]["large"]

    data_clean = cleanup(data.copy())

    filepath = f"{music_path}/{data_clean[0]}/{data_clean[1]}"
    os.makedirs(filepath, exist_ok=True)

    response_cover = requests.get(cover_url, stream=True)

    with open(f"{filepath}/cover.jpg", 'wb') as f:
        for chunk in response_cover.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


    for i in range(len(tracklist_ids)):
        id = tracklist_ids[i]
        title = tracklist_info[i]["title"]

        info = data.copy()
        info[3] = id

        if len(info) == 4:
            info += [title, i+1]
        else:
            info[4] = title
            info[5] = i+1

        download_track(info)

    print(f"------------------------------")
    print(f"Downloaded {data[1]}")
    print(f"------------------------------")
    print()
    print()

    return 0


def download_artist(data):
    get_artist = "https://eu.qobuz.squid.wtf/api/get-artist?artist_id="

    artist_down = requests.get(f"{get_artist}{data[1]}")
    artist_data = artist_down.json()

    releases = artist_data["data"]["artist"]["releases"]

    for release in releases:
        for i in release["items"]:
            album_data = [data[0], i["title"], i["dates"]["original"], i["id"]]
            download_album(album_data)
 
    return 0


def get_tracks(data):
    tracks = []
    #        [[artist, album, date, id, track, number]

    for i in data["data"]["tracks"]["items"]:
        artist = i["album"]["artist"]["name"]
        album = i["album"]["title"]
        track = i["title"]
        date = i["album"]["release_date_original"]
        number = i["track_number"]
        id = i["id"]
        cover = i["album"]["image"]["large"]

        temp = [artist, album, date, id, track, number, cover]
        tracks.append(temp)

    return tracks

def get_albums(data):
    albums = []
    #        [[artist, id, album, date]]

    for i in data["data"]["albums"]["items"]:
        artist = i["artist"]["name"]
        album = i["title"]
        date = i["release_date_original"]
        id = i["id"]
    
        temp = [artist, album, date, id]
        albums.append(temp)

    return albums

def get_artists(data):
    artists = []
    #        [[artist, id]]

    for i in data["data"]["artists"]["items"]:
        artist = i["name"]
        artist_id = i["id"]
    
        temp = [artist, artist_id]
        artists.append(temp)

    return artists



def choices(list):
    clear_terminal()

    for i, entry in enumerate(list):
        temp=f"index:    {i+1}\n"
        if search_type!="artist":
            temp+=f"id:       {entry[3]}\n"
            if search_type=="track":
                temp+=f"number:   {entry[5]}\n"
                temp+=f"track:    {entry[4]}\n"
            temp+=f"album:    {entry[1]}\n"
            temp+=f"artist:   {entry[0]}\n"
            temp+=f"date:     {entry[2]}\n"
        else:
            temp+=f"id:       {entry[1]}\n"
            temp+=f"artist:   {entry[0]}\n"
        temp+=f"------------------------\n"

        print(temp)

    chosen = int(input("enter index: "))-1
    
    return list[chosen]




music_path = "/home/royex/media/media0"
url_down_main = "https://eu.qobuz.squid.wtf/api/download-music"

search_type = input("type: ")
query = input("search: ")

params_get = {
    "q": query,
    "offset": 0
}


data = search(query)

match search_type:
    case "track":
        list = get_tracks(data)
    case "album":
        list = get_albums(data)
    case "artist":
        list = get_artists(data)    


choice = choices(list)

match search_type:
    case "track":
        download_track(choice)
    case "album":
        download_album(choice)
    case "artist":
        download_artist(choice)

