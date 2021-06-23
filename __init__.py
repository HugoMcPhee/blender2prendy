# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "blendergametools",
    "author": "Hugo McPhee",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

from .models import models
from .places import places
from .quick_cam_switch import register_quick_cam_switch, unregister_quick_cam_switch


def register():
    print("registerrigngngn")
    models.register_models()
    places.register_places()
    register_quick_cam_switch()


def unregister():
    print("unregisterrigngn")
    models.unregister_models()
    places.unregister_places()
    unregister_quick_cam_switch()
