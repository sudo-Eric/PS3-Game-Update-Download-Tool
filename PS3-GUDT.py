# -*- coding: utf-8 -*-
import os
import argparse
import urllib.request
import urllib3
import xmltodict
import hashlib
import yaml

version = "PS3-Game-Update-Download-Tool v1.0"

PS3GameUpdateDataURL = "https://a0.ww.np.dl.playstation.net/tpl/np/%s/%s-ver.xml"


def getxml(url):
    urllib3.disable_warnings()
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')

    response = http.request('GET', url)
    try:
        data = xmltodict.parse(response.data)
        return data
    except:
        # print("Failed to parse xml from response (%s)" % traceback.format_exc())
        return None


def sha1sumChecker(file_name, sha1sum):
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    sha1 = hashlib.sha1()

    with open(file_name, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    # print("SHA1: {0}".format(sha1.hexdigest()))
    return sha1.hexdigest() == sha1sum


def formatByteSize(n):
    n = int(n)
    sizeDesignator = "B"
    if n > 1000:
        n = round(n / 1000, 2)
        sizeDesignator = "KB"
    if n > 1000:
        n = round(n / 1000, 2)
        sizeDesignator = "MB"
    if n > 1000:
        n = round(n / 1000, 2)
        sizeDesignator = "GB"
    return str(n) + sizeDesignator


def removeIllegalFileNameCharacters(filename):
    return filename.replace(":", "-").replace("\n", " ").replace("/", "-").replace("*", "-").replace("?", " ")\
        .replace("\"", "'").replace("<", "-").replace(">", "-")


def downloadPackage(package, downloadFolder, overwriteExistingFiles):
    packageURL = package["@url"]
    packageName = package["@url"].split("/")[-1]
    print(" * Downloading version %s: \"%s\" (%s)" %
          (package["@version"], packageURL, formatByteSize(package["@size"])))

    if not os.path.exists(downloadFolder):
        os.makedirs(downloadFolder)
    if os.path.exists(downloadFolder + os.path.sep + packageName) and not overwriteExistingFiles:
        print("\t+File already exists. Skipping.")
        return
    urllib.request.urlretrieve(packageURL, downloadFolder + os.path.sep + packageName)

    # print("\t+Comparing file hash...", end="")
    # print("Pass") if sha1sumChecker(downloadFolder + os.path.sep + packageName, package["@sha1sum"]) else print("Fail")


def main(game_ID, downloadFolder, overwriteExistingFiles):
    if not downloadFolder[-1] == os.path.sep:
        downloadFolder += os.path.sep
    game_ID = game_ID.upper()
    print("Retrieving update data for \"%s\" from \"%s\"" % (game_ID, PS3GameUpdateDataURL % (game_ID, game_ID)))
    xml = getxml(PS3GameUpdateDataURL % (game_ID, game_ID))
    if xml is None:
        print("There are no updates available for this game")
        return
    if type(xml["titlepatch"]["tag"]["package"]) is list:
        gameName = removeIllegalFileNameCharacters(xml["titlepatch"]["tag"]["package"][-1]["paramsfo"]["TITLE"])
        print("Updates were found for \"%s\"" % gameName)
        downloadFolder += ("%s [%s] Updates" % (gameName, game_ID))
        for package in xml["titlepatch"]["tag"]["package"]:
            downloadPackage(package, downloadFolder, overwriteExistingFiles)
    else:
        gameName = removeIllegalFileNameCharacters(xml["titlepatch"]["tag"]["package"]["paramsfo"]["TITLE"])
        print("Updates were found for \"%s\"" % gameName)
        downloadFolder += ("%s [%s] Updates" % (gameName, game_ID))
        package = xml["titlepatch"]["tag"]["package"]
        downloadPackage(package, downloadFolder, overwriteExistingFiles)
    print("All updates have been downloaded!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=version)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--game_id", dest="gameID", default=None,
                       help="ID of PlayStation 3 game (eg. BCUS98114)")
    group.add_argument("--game_list", dest="gameList", default=None,
                       help="Path to the games.yml file created by RPCS3")
    parser.add_argument("--dest", dest="downloadFolder", default="PS3 Game Update Downloads",
                        help="Path to folder where downloads should be stored")
    parser.add_argument("--overwrite", dest="overwrite", action="store_true",
                        help="Overwrite existing files")
    args = parser.parse_args()

    if args.gameID is not None:
        main(args.gameID, args.downloadFolder, args.overwrite)
    else:
        with open(args.gameList) as f:
            gameIDs = yaml.load(f, Loader=yaml.loader.SafeLoader)
        for ID in gameIDs:
            main(ID, args.downloadFolder, args.overwrite)
