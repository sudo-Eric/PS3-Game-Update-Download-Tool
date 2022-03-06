# PS3 Game Update Download Tool
A tool to make it easier to download game update packages for PlayStation 3 games
This tool was mainly created with the [RPCS3](https://rpcs3.net) PlayStation 3 emulator in mind

There are three main use cases for this tool.
1. You want to download updates for a single game (or one game at a time)
2. You want to download updates for all of your games at once
3. Getting a list of download links for game updates to be downloaded separately

### How to use:
This script was designed to run from the command line and works like any other command line utility.

### Command line arguments:
-h, --help: Display help information\
-v, --version: Display script version\
--game_id: ID of the game to download updates for (e.g. BCUS98114)\
--game_list: Path to the games.yml file created by RPCS3\
--dest: Path to the folder in which you want your game updates to be saved to (defaults to current working directory)\
--overwrite: Overwrite existing files (Default behavior is to skip existing files)\
--store: Create list of update download links instead of downloading updates directly

### Dependencies:
This script requires urllib3, xmltodict, and PyYAML. These can be installed using PIP.
