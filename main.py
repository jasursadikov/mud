#!/usr/bin/env python3
import sys

import utils
import settings
from mud import Mud

if __name__ == '__main__':
    try:
        utils.settings = settings.Settings(utils.SETTINGS_FILE_NAME)
        utils.set_up()
        mud = Mud()
        mud.run()
    except KeyboardInterrupt:
        utils.print_error('Stopped by user.')