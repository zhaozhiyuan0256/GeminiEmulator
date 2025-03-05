from constellation_system import ConstellationSystem

TLES_FILEPATH = (
    "./data/three.tle"
)
FACILITIES_FILEPATH = "./data/facilities.json"
ISLS_FILEPATH = "./data/three.isls"
HOSTS_FILEPATH = "./data/hosts.json"
UPDATE_INTERVAL = 100
DEBUG_MODE = True


if __name__ == "__main__":
    cs = ConstellationSystem(
        TLES_FILEPATH,
        FACILITIES_FILEPATH,
        ISLS_FILEPATH,
        HOSTS_FILEPATH,
        UPDATE_INTERVAL,
        DEBUG_MODE,
    )
    cs.run()
