import configparser


def createConfig(path):
    """
    Create a config file
    """
    config = configparser.ConfigParser()
    config.add_section("global_settings")
    config.set("global_settings", "item0", "value0")
    config.set("global_settings", "item1", "value1")
    config.add_section("projects")
    config.set("projects", "item0", "value0")
    config.set("projects", "item1", "value1")

    with open(path, "w") as conf_file:
        config.write(conf_file)

def readConfig(path):
    config = configparser.ConfigParser()
    


# if __name__ == "__main__":
#     path = "settings.ini"
#     createConfig(path)