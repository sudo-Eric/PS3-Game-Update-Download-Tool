# -*- coding: utf-8 -*-
import os
import argparse
import traceback
import urllib.request
import urllib3
import xmltodict
import hashlib
import yaml
import datetime

version = "PS3-Game-Update-Download-Tool v1.2"

PS3GameUpdateDataURL = "https://a0.ww.np.dl.playstation.net/tpl/np/%s/%s-ver.xml"

args = None
logFile = None


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
    logFile.write("Beginning download of %s (%s)\n" % (packageName, formatByteSize(package["@size"])))
    # If download folder does not exist, create it
    if not os.path.exists(downloadFolder):
        logFile.write(" * Creating directory \"%s\"" % downloadFolder)
        os.makedirs(downloadFolder)
    # If file already exists and file overwriting is disabled, skip it
    if os.path.exists(downloadFolder + os.path.sep + packageName) and not overwriteExistingFiles:
        print("\t+ File already exists. Skipping.")
        logFile.write(" * File already exists for version %s. Skipping.\n" % package["@version"])
        return
    logFile.write(" * Version %s: %s\n" % (package["@version"], packageURL))
    # Make sure log file is written before starting a download
    logFile.flush()
    os.fsync(logFile.fileno())
    # Download update file
    urllib.request.urlretrieve(packageURL, downloadFolder + os.path.sep + packageName)

    # File hashes appear to always be different. Unsure why.
    # print("\t+Comparing file hash...", end="")
    # print("Pass") if sha1sumChecker(downloadFolder + os.path.sep + packageName, package["@sha1sum"]) else print("Fail")


def main(game_ID, downloadFolder, overwriteExistingFiles=False):
    if not downloadFolder[-1] == os.path.sep:
        downloadFolder += os.path.sep
    game_ID = game_ID.upper()
    print("Retrieving update data for \"%s\" from \"%s\"" % (game_ID, PS3GameUpdateDataURL % (game_ID, game_ID)))
    logFile.write("Retrieving update data for \"%s\" from \"%s\"\n" % (game_ID, PS3GameUpdateDataURL % (game_ID, game_ID)))
    xml = getxml(PS3GameUpdateDataURL % (game_ID, game_ID))
    logFile.write("Data retrieved: ")
    # If the XML file does not exist, no updates are available
    if xml is None:
        print("There are no updates available for this game")
        logFile.write("There are no updates available for this game\n")
        return
    # If there are multiple updates for a game
    if type(xml["titlepatch"]["tag"]["package"]) is list:
        gameName = removeIllegalFileNameCharacters(xml["titlepatch"]["tag"]["package"][-1]["paramsfo"]["TITLE"])
        print("Updates were found for \"%s\"" % gameName)
        logFile.write("Updates were found for \"%s\"\n" % gameName)
        downloadFolder += ("%s [%s] Updates" % (gameName, game_ID))
        for package in xml["titlepatch"]["tag"]["package"]:
            if args.downloadUpdates:
                downloadPackage(package, downloadFolder, overwriteExistingFiles)
            else:
                f = open(downloadFolder + "update_links.txt", "a")
                f.write(package["@url"])
                f.close()
    # If there is only one update for a game
    else:
        gameName = removeIllegalFileNameCharacters(xml["titlepatch"]["tag"]["package"]["paramsfo"]["TITLE"])
        logFile.write("Updates were found for \"%s\"\n" % gameName)
        print("Updates were found for \"%s\"" % gameName)
        downloadFolder += ("%s [%s] Updates" % (gameName, game_ID))
        package = xml["titlepatch"]["tag"]["package"]
        if args.downloadUpdates:
            downloadPackage(package, downloadFolder, overwriteExistingFiles)
        else:
            f = open(downloadFolder + ".txt", "a")
            f.write(package["@url"] + "\n")
            f.close()
    print("All updates have been downloaded!")


if __name__ == '__main__':
    #global args, logFile
    # Set up argument parser
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
    parser.add_argument("--store", dest="downloadUpdates", action="store_false",
                        help="Create list of update download links instead of downloading updates directly")
    # Parse arguments
    args = parser.parse_args()

    # Set up log file
    logFile = open('log.txt', 'a', encoding="utf-8")
    logFile.write(("#"*120) + "\n")
    logFile.write("Script (%s) started at %s (Local %s)\n" %
                  (version, datetime.datetime.utcnow().isoformat(), datetime.datetime.now().isoformat()))
    logFile.write("Inputs: game_id %s\tgame_list %s\tdest %s\toverwrite %s\n" %
                  (args.gameID, args.gameList, args.downloadFolder, args.overwrite))
    logFile.write(("#" * 120) + "\n")

    # Download a specific games updates
    if args.gameID is not None:
        main(args.gameID, args.downloadFolder, args.overwrite)
    # Download updates for multiple games at a time
    else:
        with open(args.gameList) as f:
            gameIDs = yaml.load(f, Loader=yaml.loader.SafeLoader)
        logFile.write("Loaded games list from %s\n" % args.gameList)
        for ID in gameIDs:
            main(ID, args.downloadFolder, args.overwrite)

    logFile.close()
